#include <iostream>
#include <fstream>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <string>
#include <filesystem>
#include <sstream>

using namespace std;

int main() {
    // Path to beatmap distribution folder
    string path = "B:\\Projects\\osu-sim\\dists";
    vector<double> angle_bucket_bounds = {15.0, 75.0, 130.0};
    vector<double> time_bucket_bounds = {128.0, 275.0, 424.0};
    vector<double> distance_bucket_bounds = {7.0, 67.0, 117.0};

    // Create an output csv file
    ofstream dataset_file;
    dataset_file.open("dataset.csv");

    // Get the number of total files in the directory
    int num_files = 0;
    for (const auto & entry : filesystem::directory_iterator(path)) {
        num_files++;
    }

    // Write column headers to the csv file
    dataset_file << "BeatmapID,";
    dataset_file << "Angle_0,Angle_1,Angle_2,Angle_3,";
    dataset_file << "Time_0,Time_1,Time_2,Time_3,";
    dataset_file << "Distance_0,Distance_1,Distance_2,Distance_3\n";

    int i = 0;
    for (const auto & entry : filesystem::directory_iterator(path)) {
        // Print the progress.
        cout << "\r" << "Progress: " << i+1 << "/" << num_files;
        ifstream file(entry.path());
        if (file.is_open()) {
            vector<int> angle_buckets = {0, 0, 0, 0};
            vector<int> time_buckets = {0, 0, 0, 0};
            vector<int> distance_buckets = {0, 0, 0, 0};

            // For each line in the file, split the line by commas and print the first element
            string line;
            while (getline(file, line)) {
                // If the line is empty, skip it
                if (line.empty())
                    continue;
                // Split the line by commas
                vector<string> split_line;
                stringstream ss(line);
                while (ss.good()) {
                    string substr;
                    getline(ss, substr, ',');
                    split_line.push_back(substr);
                }
                double angle = stod(split_line[0]);
                double time = stod(split_line[1]);
                double distance = stod(split_line[2]);

                if (angle < angle_bucket_bounds[0]) {
                    angle_buckets[0]++;
                } else if (angle < angle_bucket_bounds[1]) {
                    angle_buckets[1]++;
                } else if (angle < angle_bucket_bounds[2]) {
                    angle_buckets[2]++;
                } else {
                    angle_buckets[3]++;
                }

                if (time < time_bucket_bounds[0]) {
                    time_buckets[0]++;
                } else if (time < time_bucket_bounds[1]) {
                    time_buckets[1]++;
                } else if (time < time_bucket_bounds[2]) {
                    time_buckets[2]++;
                } else {
                    time_buckets[3]++;
                }

                if (distance < distance_bucket_bounds[0]) {
                    distance_buckets[0]++;
                } else if (distance < distance_bucket_bounds[1]) {
                    distance_buckets[1]++;
                } else if (distance < distance_bucket_bounds[2]) {
                    distance_buckets[2]++;
                } else {
                    distance_buckets[3]++;
                }
            }
            file.close();

            int angle_total = angle_buckets[0] + angle_buckets[1] + angle_buckets[2] + angle_buckets[3];
            int time_total = time_buckets[0] + time_buckets[1] + time_buckets[2] + time_buckets[3];
            int distance_total = distance_buckets[0] + distance_buckets[1] + distance_buckets[2] + distance_buckets[3];

            vector<double> angle_props = {0.0, 0.0, 0.0, 0.0};
            vector<double> time_props = {0.0, 0.0, 0.0, 0.0};
            vector<double> distance_props = {0.0, 0.0, 0.0, 0.0};

            for (int i = 0; i < 4; i++) {
                angle_props[i] = (double)angle_buckets[i] / angle_total;
                time_props[i] = (double)time_buckets[i] / time_total;
                distance_props[i] = (double)distance_buckets[i] / distance_total;
            }

            // Write the beatmap ID to the csv file (strip the .dist extension)
            dataset_file << entry.path().stem() << ",";
            // Write the angle proportions to the csv file
            for (int i = 0; i < 4; i++) {
                dataset_file << angle_props[i] << ",";
            }
            // Write the time proportions to the csv file
            for (int i = 0; i < 4; i++) {
                dataset_file << time_props[i] << ",";
            }
            // Write the distance proportions to the csv file
            for (int i = 0; i < 4; i++) {
                dataset_file << distance_props[i] << ",";
            }
            dataset_file << "\n";
        } else {
            printf("Unable to open file\n");
        }
        i++;
    }
    dataset_file.close();
    return 0;
}
