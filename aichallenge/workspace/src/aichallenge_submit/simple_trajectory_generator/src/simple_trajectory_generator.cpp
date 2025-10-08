// Copyright 2023 Tier IV, Inc. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <rclcpp/rclcpp.hpp>
#include <autoware_auto_planning_msgs/msg/trajectory.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/quaternion.hpp>
#include <geometry_msgs/msg/pose_with_covariance_stamped.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <sstream>

using Trajectory = autoware_auto_planning_msgs::msg::Trajectory;
using TrajectoryPoint = autoware_auto_planning_msgs::msg::TrajectoryPoint;

class CSVToTrajectory : public rclcpp::Node
{
public:
  CSVToTrajectory() : Node("csv_to_trajectory_node"), switched_to_second_path_(false), region_pass_count_(0), was_in_region_(false)
  {
    const auto rb_qos = rclcpp::QoS(rclcpp::KeepLast(1)).durability_volatile().best_effort();
    pub_ = this->create_publisher<Trajectory>("trajectory", rb_qos);
    set_parameter_callback_handle_ = this->add_on_set_parameters_callback(
      std::bind(&CSVToTrajectory::on_parameter_event, this, std::placeholders::_1));

    // 複数のCSVファイルパスを宣言
    declare_parameter<std::vector<std::string>>("csv_paths", std::vector<std::string>{});
    z_= declare_parameter<float>("z");
    
    auto csv_paths = get_parameter("csv_paths").as_string_array();
    if (csv_paths.size() != 2) {
      RCLCPP_ERROR(get_logger(), "csv_paths must contain exactly 2 paths.");
      return;
    }

    csv_paths_ = csv_paths;
    current_csv_index_ = 0;

    if (!loadCSVTrajectory(csv_paths_[current_csv_index_])) {
      RCLCPP_ERROR(get_logger(), "Failed to load initial CSV file: %s", csv_paths_[current_csv_index_].c_str());
      return;
    }

    RCLCPP_INFO(get_logger(), "Loaded initial trajectory from: %s", csv_paths_[current_csv_index_].c_str());

    // AWSIM statusのサブスクライバーを追加
    sub_status_ = create_subscription<geometry_msgs::msg::PoseWithCovarianceStamped>(
      "/sensing/gnss/pose_with_covariance", rclcpp::QoS{1}.best_effort(),
      std::bind(&CSVToTrajectory::statusCallback, this, std::placeholders::_1));

    timer_ = this->create_wall_timer(
      std::chrono::seconds(1),
      std::bind(&CSVToTrajectory::publish_trajectory, this));

  }

private:
  bool loadCSVTrajectory(const std::string & csv_path)
  {
    std::ifstream file(csv_path);
    if (!file.is_open()) {
      return false;
    }
    
    std::string line;
    std::getline(file, line);
    
    csv_trajectory_.header.stamp = this->now();
    csv_trajectory_.header.frame_id = "map";

    csv_trajectory_.points.clear();
    
    while (std::getline(file, line)) {
      std::stringstream ss(line);
      std::string token;
      std::vector<double> values;
      
      while (std::getline(ss, token, ',')) {
        values.push_back(std::stod(token));
      }
      
      if (values.size() != 8) {
        RCLCPP_WARN(get_logger(), "Invalid CSV line format, expected 8 values");
        continue;
      }
      
      TrajectoryPoint point;
      point.pose.position.x = values[0];
      point.pose.position.y = values[1];
      point.pose.position.z = z_;

      point.pose.orientation.x = values[3];
      point.pose.orientation.y = values[4];
      point.pose.orientation.z = values[5];
      point.pose.orientation.w = values[6];
      
      point.longitudinal_velocity_mps = values[7];
      
      point.lateral_velocity_mps = 0.0;
      point.acceleration_mps2 = 0.0;
      point.heading_rate_rps = 0.0;
      
      csv_trajectory_.points.push_back(point);
    }
    
    return !csv_trajectory_.points.empty();
  }

  // 指定した領域内に座標があるかどうかを判定する関数
  bool isInRegion(const geometry_msgs::msg::PoseWithCovarianceStamped::SharedPtr pose_msg, 
                  double min_x, double max_x, double min_y, double max_y)
  {
    const double x = pose_msg->pose.pose.position.x;
    const double y = pose_msg->pose.pose.position.y;
    
    return (x >= min_x && x <= max_x && y >= min_y && y <= max_y);
  }

  void statusCallback(const geometry_msgs::msg::PoseWithCovarianceStamped::SharedPtr msg)
  {
    if (switched_to_second_path_) return;

    // 指定した領域内に座標があるかどうかを判定
    // min_x, max_x, min_y, max_y
    bool is_in_region = isInRegion(msg, 89654, 89660, 43125, 43130);
    
    // 領域外から領域内に入った瞬間を検出
    if (is_in_region && !was_in_region_) {
      region_pass_count_++;
      RCLCPP_INFO(get_logger(), "Entered region %d time(s)", region_pass_count_);
      
      // 2度目の進入時にトラジェクトリを切り替え
      if (region_pass_count_ >= 1) {
        current_csv_index_ = 1;
        if (loadCSVTrajectory(csv_paths_[current_csv_index_])) {
          switched_to_second_path_ = true;
          RCLCPP_INFO(get_logger(), "Switched to second trajectory: %s", csv_paths_[current_csv_index_].c_str());
        }
      }
    }
    
    // 現在の状態を保存
    was_in_region_ = is_in_region;
  }
  
  void publish_trajectory()
  {
    if (csv_trajectory_.points.empty()) {
      RCLCPP_WARN(get_logger(), "No trajectory points to publish");
      return;
    }
    
    csv_trajectory_.header.stamp = this->now();
    pub_->publish(csv_trajectory_);
    RCLCPP_INFO_THROTTLE(get_logger(),*get_clock(), 60000 /*ms*/, "Published trajectory with %zu points", csv_trajectory_.points.size());
  }

  rcl_interfaces::msg::SetParametersResult on_parameter_event(
    const std::vector<rclcpp::Parameter> & parameters)
  {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;
    result.reason = "";

    for (const auto & param : parameters) {
      if (param.get_name() == "csv_paths") {
        if (param.get_type() == rclcpp::ParameterType::PARAMETER_STRING_ARRAY) {
          auto new_csv_paths = param.as_string_array();
          if (new_csv_paths.size() != 2) {
            RCLCPP_ERROR(get_logger(), "csv_paths must contain exactly 2 paths.");
            result.successful = false;
            result.reason = "csv_paths must contain exactly 2 paths.";
            continue;
          }
          
          csv_paths_ = new_csv_paths;
          current_csv_index_ = 0;
          switched_to_second_path_ = false;
          
          if (loadCSVTrajectory(csv_paths_[current_csv_index_])) {
            RCLCPP_INFO(get_logger(), "Successfully loaded new trajectory paths and reset to first trajectory");
          } else {
            RCLCPP_ERROR(get_logger(), "Failed to load new CSV file: %s", csv_paths_[current_csv_index_].c_str());
            result.successful = false;
            result.reason = "Failed to load new CSV file.";
          }
        } else {
          RCLCPP_WARN(get_logger(), "Parameter 'csv_paths' received with wrong type. Expected string array.");
          result.successful = false;
          result.reason = "Invalid type for csv_paths parameter.";
        }
      } else if (param.get_name() == "z") {
        if (param.get_type() == rclcpp::ParameterType::PARAMETER_DOUBLE || param.get_type() == rclcpp::ParameterType::PARAMETER_INTEGER) {
          z_ = static_cast<float>(param.as_double());
          RCLCPP_INFO(get_logger(), "z parameter changed to %f", z_);
        } else {
          RCLCPP_WARN(get_logger(), "Parameter 'z' received with wrong type. Expected float/double.");
          result.successful = false;
          result.reason = "Invalid type for z parameter.";
        }
      }
    }
    return result;
  }
  
  rclcpp::Publisher<Trajectory>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Subscription<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr sub_status_;
  Trajectory csv_trajectory_;
  float z_;
  std::vector<std::string> csv_paths_;
  int current_csv_index_;
  bool switched_to_second_path_;
  int region_pass_count_;  // 領域通過回数をカウント
  bool was_in_region_;  // 前回のコールバックで領域内にいたかどうか
  OnSetParametersCallbackHandle::SharedPtr set_parameter_callback_handle_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<CSVToTrajectory>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
