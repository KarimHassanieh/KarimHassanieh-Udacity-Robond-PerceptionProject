## Project: Perception Pick & Place
## [Rubric](https://review.udacity.com/#!/rubrics/1067/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!
[//]: # (Image References)

[image1]: ./Images/clusterd2.png
[image2]: ./Images/clustered1.png


### Exercise 1, 2 and 3 pipeline implemented
Excercise 1,2,3 implemented in '**PR2_pickplace.py**' python script which you can refer.
#### 1. Complete Exercise 1 steps. Pipeline for filtering and RANSAC plane fitting implemented.
Implemented in the following order to the raw pointcloud data :

1-Statistical Outlier Filtering, with a set mean equal to 10 and standard deviation threshold equal to 0.001

2-Voxel grid downsampling with a leaf size equal to 0.01

3-A passthrough filter was implement, Z axis between 0.45 and 0.85, X axis between 0.33 and 0.9

4-RANSAC filtering was implemented with a maximuim distance of 0.01
#### 2. Complete Exercise 2 steps: Pipeline including clustering for segmentation implemented.  
Clustering was preformed with the following parameters taken into consideration : 
Cluster Tolerance | Min Cluster Size | Max Cluster Size
--- | --- | --- | ---
1 | 0.05 | 50 | 200,000

The following images are the results obtained

![alt text][image1]
![alt text][image2]

#### 2. Complete Exercise 3 Steps.  Features extracted and SVM trained.  Object recognition implemented.
Here is an example of how to include an image in your writeup.

![demo-1](https://user-images.githubusercontent.com/20687560/28748231-46b5b912-7467-11e7-8778-3095172b7b19.png)




Here's | A | Snappy | Table
--- | --- | --- | ---
1 | `highlight` | **bold** | 7.41
2 | a | b | c
3 | *italic* | text | 403
4 | 2 | 3 | abcd


### Pick and Place Setup

#### 1. For all three tabletop setups (`test*.world`), perform object recognition, then read in respective pick list (`pick_list_*.yaml`). Next construct the messages that would comprise a valid `PickPlace` request output them to `.yaml` format.

And here's another image! 
![demo-2](https://user-images.githubusercontent.com/20687560/28748286-9f65680e-7468-11e7-83dc-f1a32380b89c.png)

Spend some time at the end to discuss your code, what techniques you used, what worked and why, where the implementation might fail and how you might improve it if you were going to pursue this project further.  



