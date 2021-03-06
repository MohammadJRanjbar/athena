# Adversarial Defense as a Framework

[Machine learning systems](https://pooyanjamshidi.github.io/mls/) have achieved impressive success in a wide range of domains like computer vision and natural langurage processing. However, their vulnerability to adversarial examples can lead to a series of consequences, especially in security-critical tasks. For example, an object detector on a self-driving vehicle may incorrectly recognize [an stop sign as a speed limit](https://spectrum.ieee.org/cars-that-think/transportation/sensors/slight-street-sign-modifications-can-fool-machine-learning-algorithms). 

The threat of the adversarial examples has inspired a sizable body of research on various defense techniques. With the assumption on the specific known attack(s), most of the existing defenses, although effective against particular attacks, can be circumvented under slightly different conditions, either a stronger adaptive adversary or in some cases even weak (but different) adversaries. In order to stop the `arms race` between the attacks and defenses, we wonder

> How can we, instead, design a defense, not as a technique, but as a framework that one can construct a specific defense considering the niche tradeoff space of robustness one may want to achieve as well as the cost one is willing to pay to achieve that level of robustness?

[**ATHENA: A Framework based on Diverse Weak Defenses for Building Adversarial Defense**](https://softsys4ai.github.io/athena/) \
[Ying Meng](https://meng2010.github.io/), [Jianhai Su](https://oceank.github.io/), [Jason M O'Kane](https://www.cse.sc.edu/~jokane/), [Pooyan Jamshidi](https://pooyanjamshidi.github.io/)


<table>
    <tr>
        <td><center><a href="https://arxiv.org/abs/2001.00308"><img height="100" width="78" src="www/athena_preprint.png" style="border:1px solid" style="border:1px solid black"><br>arXiv Preprint</a></center></td>
        <td><center><a href="https://github.com/softsys4ai/athena"><img height="100" width="78" src="www/athena_website.png" style="border:1px solid" style="border:1px solid black"><br>Website</a></center></td>
        <td><center><a href="https://github.com/csce585-mlsystems/project-athena" class="d-inline-block p-3 align-top"><img height="100" width="78" src="www/class_project.png" style="border:1px solid black"><br>CSCE 585<br>Project</a></center></td>
        <td><center><a href="https://github.com/csce585-mlsystems/project-athena/blob/master/notebooks/Task1_GenerateAEs_ZeroKnowledgeModel.ipynb" class="d-inline-block p-3 align-top"><img height="100" width="78" src="www/tutorial_craftAE_zk.png" style="border:1px solid black"><br>Hello World<br>Tutorial</a></center></td>
    </tr>
</table>

## ATHENA: a Framework for Building Adversarial Defense
**ATHENA** (Goddess of defense in Greek mythology) is an `extensible framework` for building `generic` (and thus, broadly applicable) yet `effective defense against adversarial attacks`.

The design philosophy behind ATHENA is based on ensemble of many `diverse weak defenses` (WDs), where each WD, the building blocks of the framework, is a machine learning classifier (e.g., DNN, SVM) that first applies a transformation on the original input and then produces an output for the transformed input. Given an input, an ensemble first collects predicted outputs from all of the WDs and then determines the final output, using some ensemble strategy such as majority voting or averaging the predicted outputs from the WDs.  

<p align="center">
  <img width="500px" height="auto" src="www/athena_wk_train.png">
  <img width="500px" height="auto" src="www/athena_wk_test.png">
</p>


--------
## Insights: Weak Defenses Complements Each Other!

In computer vision, a transformation is an image processing function. By distorbing its input, a transformation changes the adversarial optimized perturbations and thus making the perturbations less effective. However, the effectiveness of a single type of transformation varies on attacks and datasets. By mitigating the perturbations in different ways such as adjusting angles or position of the input, adding or removing noises, a collection of diverse transformations provides robustness against various attacks. Thus, the `Diverse ensemble` achieves the lowest error rate in most cases, especially for tasks on CIFAR-100. 

<p align="center">
  <img width="500px" height="auto" src="www/trans_as_wd.png">
</p>


Ensembling diverse transformations can result in a robust defense against a variety of attacks and provide a `tradeoff space`, where one can build a `more robust` ensemble by adding more transformations or building an ensemble with `lower overhead and cost` by utilizing fewer transformations.

<p align="center">
  <img width="800px" height="auto" src="www/athena_motivation.png">
</p>

--------

## Zero Knowledge Threat Model
##### Adversary knows everything about the model, but it does not know there is a defense in place!

The effectiveness of individual WDs (each associated to a transformation) varies across attack methods and magnitudes of an attack. While a large population of transformations from a variety of categories successfully disentangle adversarial perturbations generated by various attacks. The variation of individual WDs' error rates spans wider as the perturbation magnitude become stronger for a selected attack. By utilizing many diverse transformations, with ATHENA, we build effective ensembles that outperform the two state-of-the-art defenses --- PGD adversarial training (PGD-ADT) and randomly smoothing (RS), in all cases.

<p align="center">
  <img width="800px" height="auto" src="www/eval_cifar100_zk.png">
</p>

## Black-box Threat Model
##### Adversary does not have access to the model but it can query the model.

### Transfer-based approach

Although the transferability rate increases as the budget increases, the drop in the transferability rate from the undefended model (UM) to ATHENA indicates that ATHENA is less sensitive to the perturbation. Ensembling from many diverse transformations provides tangible benefits in blocking the adversarial transferability between weak defenses, and thus enhances model's robustness against the transfer-based black-box attack. 

<!-- ![evaluations against transfer-based black-box attack](images/eval_bb_trans.png){:width="680px" height=auto} 
 -->
<p align="center">
  <img width="800px" height="auto" src="www/eval_bb_trans.png">
</p>


### Gradient-direction-estimation-based approach

Hop-Skip-Jump attack (HSJA) generates adversarial examples by querying the output labels from the target model for the perturbed images. Compared to that generated based on the UM, the adversarial examples generated based on ATHENA are much further away from the corresponding benign samples. As the query budget increases, the distances of the UM-targeted AEs drop much more significantly than that of the ATHENA-targeted AEs. Therefore, ATHENA increases the chance of such AEs being detected by even a simple detection mechanism.

<!-- ![evaluations against hsja attack](images/eval_bb_hsja.png){:width="480px" height=auto} ![hsja samples](images/samples_cifar100_bb_linf.png){:width="320px" height="auto"}
 -->
<p align="center">
  <img width="800px" height="auto" src="www/eval_bb_hsja.png">
  <img width="800px" height="auto" src="www/samples_cifar100_bb_linf.png">
</p>


## White-box Threat Model
##### Adversary knows everything about the model and defense in place!

### Greedy approach

As expected, stronger AEs are generated by the greedy white-box attack with a looser constraint on the dissimilarity threshold. However, such success comes at a price: with the largest threshold, the greedy attack has to spend 310X more time to generate adversarial example for a single input. This provides a tradeoff space, where realizations of ATHENA that employ larger ensembles incur more cost to the adversaries and they will eventually give up! Moreover, the generated AEs are heavily distored and very likely to be detected either by a human or an automated detection mechanism.

<p align="center">
    <img width="350px" height="auto" src="www/eval_wb_greedy.png">
    <img width="350px" height="auto" src="www/samples_cifar100_wb.png">
</p>
<p align="center">
    <img width="350px" height="auto" src="www/eval_wb_cost.png">
    <img width="350px" height="auto" src="www/eval_wb_detector.png">
</p>


### Optimization-based approach

As the adversary have access to more WDs, it can launch more successful attacks without even increasing the perturbations. However, the computational cost of AE generation increases as well. The attacker has the choice to sample more random transformations and a choice to a distribution of a large population and diverse transformations in order to generate stronger AEs. However, this will incur a larger computational cost as well.

<!-- ![evaluations against optimization-based white-box attack](images/eval_wb_optimization.png){:width="460px" height=auto} -->

<p align="center">
  <img width="350px" height="auto" src="www/eval_wb_optimization_error.png">
  <img width="360px" height="auto" src="www/eval_wb_optimization_time.png">
</p>

--------
## Acknowledgement
- <img alt="google cloud" src="www/google_cloud.png" width="25px" height="auto"> Google via GCP cloud research credits
- <img alt="NASA" src="www/nasa-logo-web-rgb.png" width="25px" height="auto"> NASA (EPSCoR 521340-SC001)
- <img alt="UofSC" src="www/usc_logo.png" width="25px" height="auto"> Research Computing Center at the University of South Carolina
- <img alt="ChameleonCloud" src="www/chameleoncloud_logo.png" width="25px" height="auto"> Chameleon Cloud via GPU compute nodes


--------
## How to Cite

### Citation

Ying Meng, Jianhai Su, Jason M O'Kane, and Pooyan Jamshidi. *ATHENA: A Framework based on Diverse Weak Defenses for Building Adversarial Defense*. arXiv preprint arXiv: 2001.00308, 2020.


### Bibtex
```ruby
@article{meng2020athena,
      title={ATHENA: A Framework based on Diverse Weak Defenses for Building Adversarial Defense},
      author={Ying Meng and Jianhai Su and Jason M O'Kane and Pooyan Jamshidi},
      journal={arXiv preprint arXiv:2001.00308},
      year={2020}
}
```
