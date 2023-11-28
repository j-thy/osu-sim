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
    string path = "B:\\Projects\\osu-sim\\sliders";
    vector<double> slider_length_bucket_bounds = {53.0, 123.0, 235.0};
    vector<double> slider_velocity_bucket_bounds = {0.0, 12.0, 46.0};

    // Create an output csv file
    ofstream dataset_file;
    dataset_file.open("dataset_slider.csv");

    // Get the number of total files in the directory
    int num_files = 0;
    for (const auto & entry : filesystem::directory_iterator(path)) {
        num_files++;
    }

    // Write column headers to the csv file
    dataset_file << "BeatmapID,";
    dataset_file << "SRatio,";
    dataset_file << "SLength_0,SLength_1,SLength_2,SLength_3,";
    dataset_file << "SVelocity_0,SVelocity_1,SVelocity_2,SVelocity_3\n";

    int i = 0;
    for (const auto & entry : filesystem::directory_iterator(path)) {
        // Print the progress.
        cout << "\r" << "Progress: " << i+1 << "/" << num_files;
        ifstream file(entry.path());
        if (file.is_open()) {
            vector<int> slider_length_buckets = {0, 0, 0, 0};
            vector<int> slider_velocity_buckets = {0, 0, 0, 0};

            // Write the beatmap ID to the csv file (strip the .dist extension)
            dataset_file << entry.path().stem() << ",";

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

                if (split_line.size() != 2) {
                    dataset_file << stod(line) << ",";
                    continue;
                }

                double slider_length = stod(split_line[0]);
                double slider_velocity = stod(split_line[1]);

                if (slider_length < slider_length_bucket_bounds[0]) {
                    slider_length_buckets[0]++;
                } else if (slider_length < slider_length_bucket_bounds[1]) {
                    slider_length_buckets[1]++;
                } else if (slider_length < slider_length_bucket_bounds[2]) {
                    slider_length_buckets[2]++;
                } else {
                    slider_length_buckets[3]++;
                }

                if (slider_velocity < slider_velocity_bucket_bounds[0]) {
                    slider_velocity_buckets[0]++;
                } else if (slider_velocity < slider_velocity_bucket_bounds[1]) {
                    slider_velocity_buckets[1]++;
                } else if (slider_velocity < slider_velocity_bucket_bounds[2]) {
                    slider_velocity_buckets[2]++;
                } else {
                    slider_velocity_buckets[3]++;
                }
            }
            file.close();

            int slider_length_total = slider_length_buckets[0] + slider_length_buckets[1] + slider_length_buckets[2] + slider_length_buckets[3];
            int slider_velocity_total = slider_velocity_buckets[0] + slider_velocity_buckets[1] + slider_velocity_buckets[2] + slider_velocity_buckets[3];

            vector<double> slider_length_props = {0.0, 0.0, 0.0, 0.0};
            vector<double> slider_velocity_props = {0.0, 0.0, 0.0, 0.0};

            for (int i = 0; i < 4; i++) {
                if (slider_length_total != 0)
                    slider_length_props[i] = (double)slider_length_buckets[i] / slider_length_total;
                if (slider_velocity_total != 0)
                    slider_velocity_props[i] = (double)slider_velocity_buckets[i] / slider_velocity_total;
            }

            // Write the slider length proportions to the csv file
            for (int i = 0; i < 4; i++) {
                dataset_file << slider_length_props[i] << ",";
            }
            // Write the slider velocity proportions to the csv file
            for (int i = 0; i < 4; i++) {
                if (i == 3)
                    dataset_file << slider_velocity_props[i] << "\n";
                else
                    dataset_file << slider_velocity_props[i] << ",";
            }
        } else {
            printf("Unable to open file\n");
        }
        i++;
    }
    dataset_file.close();
    return 0;
}
