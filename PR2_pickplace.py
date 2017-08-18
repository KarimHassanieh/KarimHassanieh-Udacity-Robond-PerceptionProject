#!/usr/bin/env python

# Import modules
import numpy as np
import sklearn
from sklearn.preprocessing import LabelEncoder
import pickle
from sensor_stick.srv import GetNormals
from sensor_stick.features import compute_color_histograms
from sensor_stick.features import compute_normal_histograms
from visualization_msgs.msg import Marker
from sensor_stick.marker_tools import *
from sensor_stick.msg import DetectedObjectsArray
from sensor_stick.msg import DetectedObject
from sensor_stick.pcl_helper import *
import rospy
import tf
from geometry_msgs.msg import Pose
from std_msgs.msg import Float64
from std_msgs.msg import Int32
from std_msgs.msg import String
from pr2_robot.srv import *
from rospy_message_converter import message_converter
import yaml


# Helper function to get surface normals
def get_normals(cloud):
    get_normals_prox = rospy.ServiceProxy('/feature_extractor/get_normals', GetNormals)
    return get_normals_prox(cloud).cluster

# Helper function to create a yaml friendly dictionary from ROS messages
def make_yaml_dict(test_scene_num, arm_name, object_name, pick_pose, place_pose):
    yaml_dict = {}
    yaml_dict["test_scene_num"] = test_scene_num.data
    yaml_dict["arm_name"]  = arm_name.data
    yaml_dict["object_name"] = object_name.data
    yaml_dict["pick_pose"] = message_converter.convert_ros_message_to_dictionary(pick_pose)
    yaml_dict["place_pose"] = message_converter.convert_ros_message_to_dictionary(place_pose)
    return yaml_dict

# Helper function to output to yaml file
def send_to_yaml(yaml_filename, dict_list):
    data_dict = {"object_list": dict_list}
    with open(yaml_filename, 'w') as outfile:
        yaml.dump(data_dict, outfile, default_flow_style=False)

# Callback function for your Point Cloud Subscriber
def pcl_callback(pcl_msg):

# Exercise-2 TODOs:

    # TODO: Convert ROS msg to PCL data
    original_cloud=ros_to_pcl(pcl_msg)    
    # TODO: Statistical Outlier Filtering
    outlier_filter =(original_cloud).make_statistical_outlier_filter()
    outlier_filter.set_mean_k(10)
    outlier_filter.set_std_dev_mul_thresh(0.001)
    filtered_cloud = outlier_filter.filter()
    # TODO: Voxel Grid Downsampling
    vox=filtered_cloud.make_voxel_grid_filter()
    LEAF_SIZE=0.01
    vox.set_leaf_size(LEAF_SIZE,LEAF_SIZE,LEAF_SIZE)
    vox_cloud=vox.filter()
    # TODO: PassThrough Filter
    #REMOVE UNDERNEATH TABLE 
    passthrough = vox_cloud.make_passthrough_filter()
    filter_axis = 'z'
    passthrough.set_filter_field_name(filter_axis)
    axis_min = 0.45
    axis_max = 0.85
    passthrough.set_filter_limits (axis_min, axis_max)
    passthrough_cloud= passthrough.filter()
    #REMOVE EDGES OF TABLE 
    passthrough = passthrough_cloud.make_passthrough_filter()
    filter_axis = 'x'
    passthrough.set_filter_field_name(filter_axis)
    axis_min = 0.33
    axis_max = 0.9
    passthrough.set_filter_limits (axis_min, axis_max)
    passthrough_cloud= passthrough.filter()
    # TODO: RANSAC Plane Segmentation
    seg = passthrough_cloud.make_segmenter()
    seg.set_model_type(pcl.SACMODEL_PLANE)
    seg.set_method_type(pcl.SAC_RANSAC)
    max_distance=0.01
    seg.set_distance_threshold(max_distance)
    inliers, coefficients = seg.segment()
    # TODO: Extract inliers and outliers
    table_cloud = passthrough_cloud.extract(inliers, negative=False)
    objects_cloud = passthrough_cloud.extract(inliers, negative=True)
    # TODO: Euclidean Clustering
    white_cloud=XYZRGB_to_XYZ(objects_cloud)
    tree= white_cloud.make_kdtree()
    ec=white_cloud.make_EuclideanClusterExtraction()
    ec.set_ClusterTolerance(0.05)
    ec.set_MinClusterSize(50)
    ec.set_MaxClusterSize(20000)
    ec.set_SearchMethod(tree)
    cluster_indices = ec.Extract()
    # TODO: Create Cluster-Mask Point Cloud to visualize each cluster separately
    cluster_color = get_color_list(len(cluster_indices))
    color_cluster_point_list = []
    for j, indices in enumerate(cluster_indices):
      for i, indice in enumerate(indices):
       color_cluster_point_list.append([white_cloud[indice][0],
                                        white_cloud[indice][1],
                                        white_cloud[indice][2],
                                         rgb_to_float(cluster_color[j])])

    objects_clustered_cloud = pcl.PointCloud_PointXYZRGB()
    objects_clustered_cloud.from_list(color_cluster_point_list)
    # TODO: Convert PCL data to ROS messages

    # TODO: Publish ROS messages
    pcl_original_cloud_pub.publish(pcl_msg)
    pcl_filtered_cloud_pub.publish(pcl_to_ros(filtered_cloud))
    pcl_voxel_cloud_pub.publish(pcl_to_ros(vox_cloud))
    pcl_passthrough_cloud_pub.publish(pcl_to_ros(passthrough_cloud))
    pcl_RANSAC_object_cloud_pub.publish(pcl_to_ros(objects_cloud))
    pcl_clustered_object_cloud_pub.publish(pcl_to_ros(objects_clustered_cloud))

    # Exercise-3 TODOs:

    # Classify the clusters! (loop through each detected cluster one at a time)
    detected_objects_labels = []
    detected_objects = []
    for index, pts_list in enumerate(cluster_indices):
     pcl_cluster = objects_cloud.extract(pts_list)
     ros_cluster=pcl_to_ros(pcl_cluster)
        # Compute the associated feature vector
     chists = compute_color_histograms(ros_cluster, using_hsv=True)
     normals = get_normals(ros_cluster)
     nhists = compute_normal_histograms(normals)
     feature = np.concatenate((chists, nhists))
        # Make the prediction
     prediction = clf.predict(scaler.transform(feature.reshape(1,-1)))
     label = encoder.inverse_transform(prediction)[0]
     detected_objects_labels.append(label)
        # Publish a label into RViz
     label_pos = list(white_cloud[pts_list[0]])
     label_pos[2] += .4
     object_markers_pub.publish(make_label(label,label_pos, index))
        # Add the detected object to the list of detected objects.
     do = DetectedObject()
     do.label = label
     do.cloud = ros_cluster
     detected_objects.append(do)
    #Publish list of detected objects
    rospy.loginfo('Detected {} objects: {}'.format(len(detected_objects_labels), detected_objects_labels))
    # Suggested location for where to invoke your pr2_mover() function within pcl_callback()
    # Could add some logic to determine whether or not your object detections are robust
    # before calling pr2_mover()
    try:
        pr2_mover(detected_objects)
    except rospy.ROSInterruptException:
        pass

# function to load parameters and request PickPlace service
def pr2_mover(object_list):

    # TODO: Initialize variables
    labels=[]
    centroids=[]
    dict_list=[]
    TEST_SCENE_NUM = Int32()
    TEST_SCENE_NUM.data=2
    OBJECT_NAME= String()
    WHICH_ARM= String()
    PICK_POSE= Pose()
    PLACE_POSE= Pose()
    # TODO: Get/Read parameters
    object_list_param = rospy.get_param('/object_list')
    dropbox_param=rospy.get_param('/dropbox')
    # TODO: Parse parameters into individual variables
    # TODO: Rotate PR2 in place to capture side tables for the collision map
    # TODO: Loop through the pick list
    for object_to_pick in object_list_param:
     OBJECT_NAME.data=object_to_pick['name']
     for detected in object_list:
      if OBJECT_NAME.data==detected.label:
        group=object_to_pick['group']
        # TODO: Get the PointCloud for a given object and obtain it's centroid
        points_arr = ros_to_pcl(detected.cloud).to_array()
        centroids = (np.mean(points_arr,axis=0)[:3])
        PICK_POSE.position.x = float(centroids[0])
        PICK_POSE.position.y = float(centroids[1])
        PICK_POSE.position.z = float(centroids[2])
        # TODO: Create 'place_pose' for the object
        for drop in dropbox_param:
         if group==drop['group']:
          PLACE_POSE.position.x = drop['position'][0]
          PLACE_POSE.position.y = drop['position'][1]
          PLACE_POSE.position.z = drop['position'][2]
        # TODO: Assign the arm to be used for pick_place
          WHICH_ARM.data=drop['name']
        # TODO: Create a list of dictionaries (made with make_yaml_dict()) for later output to yaml format
          yaml_dict = make_yaml_dict(TEST_SCENE_NUM, WHICH_ARM, OBJECT_NAME, PICK_POSE, PLACE_POSE)
          dict_list.append(yaml_dict)
        # Wait for 'pick_place_routine' service to come up
          rospy.wait_for_service('pick_place_routine')
          try:
           pick_place_routine = rospy.ServiceProxy('pick_place_routine', PickPlace)
       # TODO: Insert your message variables to be sent as a service request
           resp = pick_place_routine(TEST_SCENE_NUM, OBJECT_NAME, WHICH_ARM, PICK_POSE, PLACE_POSE)
           print ("Response: ",resp.success)
          except rospy.ServiceException, e:
           print "Service call failed: %s"%e

    # TODO: Output your request parameters into output yaml file
        send_to_yaml('output_list_2.yaml', dict_list)


if __name__ == '__main__':

    # TODO: ROS node initialization
    print ('INITIALIZING OBJECT DETECTION PROCESS')
    rospy.init_node('object_detection',anonymous=True)
    # TODO: Create Subscribers
    pcl_sub = rospy.Subscriber("/pr2/world/points", pc2.PointCloud2, pcl_callback, queue_size=1)

    # TODO: Create Publishers
    #Point cloud filtering
    pcl_original_cloud_pub = rospy.Publisher("object_detection/original_cloud", PointCloud2, queue_size=1)
    pcl_filtered_cloud_pub=rospy.Publisher("object_detection/filtered_cloud", PointCloud2, queue_size=1)
    pcl_voxel_cloud_pub=rospy.Publisher("object_detection/voxel_cloud", PointCloud2, queue_size=1)
    pcl_passthrough_cloud_pub=rospy.Publisher("object_detection/passthrough_cloud", PointCloud2, queue_size=1)
    pcl_RANSAC_object_cloud_pub=rospy.Publisher("object_detection/object_cloud", PointCloud2, queue_size=1)
    pcl_clustered_object_cloud_pub=rospy.Publisher("object_detection/clustered_cloud", PointCloud2, queue_size=1)
    #Objects detected 
    object_markers_pub = rospy.Publisher("/object_markers", Marker, queue_size=12)
    detected_objects_pub = rospy.Publisher("/detected_objects", DetectedObjectsArray, queue_size=12)
    # TODO: Load Model From disk
    model = pickle.load(open('model.sav', 'rb'))
    clf = model['classifier']
    encoder = LabelEncoder()
    encoder.classes_ = model['classes']
    scaler = model['scaler']
    # Initialize color_list
    get_color_list.color_list = []

    # TODO: Spin while node is not shutdown
    while not rospy.is_shutdown():
     rospy.spin()

