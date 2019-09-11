from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from models import *
from config import *

from scipy.optimize import differential_evolution

import numpy as np
import pandas as pd

import os

# TODO: Build out more rigorous testing for targeted and untargeted samples
# TODO: Test on more datasets and models
# TODO: Configure any logging methods for statistics that may be relevant
# TODO: Configure any more files that need reference to one-pixel-attack
# TODO: Consolidate Division by Zero RunTimeWarning
class PixelAttacker:
    def __init__(self, models, dataset):
        # Load data and model
        self.models = models
        (self.X_test, self.Y_test) = data.load_data(dataset)[1]
        # Scaling images (0 - 255)
        self.X_test *= (255.0 / self.X_test.max())
        # Formatting labels into 1-D array
        self.Y_test = np.array(
            [np.where(y == 1)[0][0] for y in self.Y_test]
        )
        self.class_names = np.unique(self.Y_test)
        self.dimensions = self.X_test.shape[1: 3]

    @staticmethod
    def perturb_image(xs, img):
        # If this function is passed just one perturbation vector,
        # packing in list to keep the computation the same
        if xs.ndim < 2:
            xs = np.array([xs])

        # Copying image n == len(xs) times to
        # create n new perturbed images
        tile = [len(xs)] + [1] * (xs.ndim + 1)
        imgs = np.tile(img, tile)

        # Flooring the members of xs as int types
        xs = xs.astype(int)

        for x, img in zip(xs, imgs):
            # Splitting x into an array of tuples (perturbation pixels)
            # i.e., [[x,y,r,g,b], ...]
            pixels = np.split(x, len(x) // len(img.shape))

            for pixel in pixels:
                # At each pixel's x,y position, assigning rgb value
                x_pos, y_pos, *rgb = pixel
                img[x_pos][y_pos] = rgb

        return imgs

    def predict_classes(self, xs, img, target_class, model, minimize=True):
        # Perturbing image with the given pixel(s) x and getting prediction of model
        imgs_perturbed = self.perturb_image(xs, img)
        predictions = model.predict(imgs_perturbed)[:, target_class]
        return predictions if minimize else 1 - predictions

    def attack_success(self, x, img, target_class, model, targeted_attack=False):
        # Perturbing image with the given pixel(s) and getting prediction of model
        attack_image = self.perturb_image(x, img)
        confidence = model.predict(attack_image)[0]
        predicted_class = np.argmax(confidence)

        # If the prediction is what we want (misclassification or
        # targeted classification), return True
        if ((targeted_attack and predicted_class == target_class) or
                (not targeted_attack and predicted_class != target_class)):
            return True

    def attack(self, img, model, target=None, pixel_count=(1,),
               maxiter=75, population=400):
        # Change the target class based on whether this is a targeted attack or not
        targeted_attack = target is not None
        target_class = target if targeted_attack else self.Y_test[img]

        # Define bounds for a flat vector of x,y,r,g,b values
        # For more pixels, repeat this layout
        dim_x, dim_y = self.X_test[img].shape[:2]
        bounds = [(0, dim_x), (0, dim_y)]
        for i in range(abs(2 - self.X_test[img].ndim)):
            bounds.append((0, 256))
        bounds = bounds * pixel_count

        # Population multiplier, in terms of the size of the perturbation vector x
        popmul = max(1, population // len(bounds))

        # Format the predict/callback functions for the differential evolution algorithm
        predict_fn = lambda xs: self.predict_classes(
            xs, self.X_test[img], target_class, model, target is None)
        callback_fn = lambda x, convergence: self.attack_success(
            x, self.X_test[img], target_class, model, targeted_attack)

        # Calling Scipy's Implementation of Differential Evolution
        attack_result = differential_evolution(
            predict_fn, bounds, maxiter=maxiter, popsize=popmul,
            recombination=1, atol=-1, callback=callback_fn, polish=False)
        # Some statistics to return from this function
        attack_image = self.perturb_image(attack_result.x, self.X_test[img])[0]
        prior_probs = model.predict(np.array([self.X_test[img]]))[0]
        predicted_probs = model.predict(np.array([attack_image]))[0]
        predicted_class = np.argmax(predicted_probs)
        actual_class = self.Y_test[img]
        success = predicted_class != actual_class
        cdiff = prior_probs[actual_class] - predicted_probs[actual_class]

        return [model.name, pixel_count, img, actual_class, predicted_class, success, cdiff, prior_probs,
                predicted_probs, attack_result.x, attack_image]

    def attack_all(self, models, samples=500, pixels=(1, 3, 5), targeted=False,
                   maxiter=75, population=400):
        results = []
        for model in models:
            model_results = []
            img_samples = np.random.choice(self.Y_test, samples)

            for pixel_count in pixels:
                for i, img in enumerate(img_samples):
                    print(model.name, '- image', img, '-', i + 1, '/', len(img_samples))
                    targets = [None] if not targeted else range(10)

                    for target in targets:
                        if targeted:
                            print('Attacking with target', self.class_names[target])
                            if target != self.Y_test[img]:
                                continue
                        result = self.attack(img, model, target, pixel_count,
                                             maxiter=maxiter, population=population)
                        model_results.append(result)

            results += model_results
        return results


def generate(model_name, attack_method, X, Y, attack_params):
    label_smoothing_rate = 0.1

    prefix, dataset, architect, trans_type = model_name.split('-')

    # flag - whether to train a clean model
    train_new_model = True
    if os.path.isfile('{}/{}.h5'.format(PATH.MODEL, model_name)):
        # found a trained model
        print('Found the trained model.')
        train_new_model = False

    img_rows, img_cols, nb_channels = X.shape[1:4]
    nb_classes = Y.shape[1]

    # Force TensorFlow to use single thread to improve reproducibility
    config = tf.ConfigProto(intra_op_parallelism_threads=1,
                            inter_op_parallelism_threads=1)
    sess = tf.Session(config=config)
    keras.backend.set_session(sess)

    # label smoothing
    Y -= label_smoothing_rate * (Y - 1. / nb_classes)

    model = None
    if train_new_model:
        print('INFO: train a new model then generate adversarial examples.')
        # create a new model
        input_shape = (img_rows, img_cols, nb_channels)
        model = create_model(dataset, input_shape=input_shape, nb_classes=nb_classes)
    else:
        # load model
        model = keras.models.load_model('{}/{}.h5'.format(PATH.MODEL, model_name))

    # to be able to call the model in the custom loss, we need to call it once before.
    # see https://github.com/tensorflow/tensorflow/issues/23769
    model(model.input)

    attacker = PixelAttacker(models=model, dataset=dataset)

    results = attacker.attack_all(models=[model],
                                  samples=attack_params['samples'],
                                  pixels=attack_params['pixel_counts'],
                                  targeted=attack_params['targeted'],
                                  maxiter=attack_params['max_iterations'],
                                  population=attack_params['population']
                                  )
    print(f"Results:\n"
          f"{results}")
    columns = ['model', 'pixels', 'image', 'true', 'predicted', 'success', 'cdiff', 'prior_probs', 'predicted_probs',
               'perturbation', 'attack_image']
    results_table = pd.DataFrame(results, columns=columns)
    attack_images = results_table['attack_image']

    print("Saving to folder")
    for index, img in enumerate(attack_images):
        from PIL import Image
        img = img.reshape((28, 28))
        img = Image.fromarray(img)
        img = img.convert('L')
        file_path = f'../{PATH.ADVERSARIAL_FILE}/example-{index}.jpeg'
        img.save(file_path)

    return (attack_images, results_table['predicted'])


if __name__ == '__main__':
    model = keras.models.load_model('../mnist/models/model-mnist-cnn-clean.h5')
    attack_params = {
        'samples': 25,
        'pixel_counts': tuple([1]),
        'max_iterations': 100,
        'targeted': True,
        'population': 400
    }
    generate(model_name='model-mnist-cnn-clean', attack_params=attack_params)
