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

int main()
{
    // Path to beatmap distributions folder
    string path = "B:\\Projects\\osu-sim\\dists";

    // Bucket bounds for each feature
    vector<double> angle_bucket_bounds = {15.0, 75.0, 130.0};
    vector<double> time_bucket_bounds = {128.0, 275.0, 424.0};
    vector<double> distance_bucket_bounds = {7.0, 67.0, 117.0};

    // Create an output CSV file
    ofstream dataset_file;
    dataset_file.open("dataset.csv");

    // Get the number of files in the directory
    int num_files = 0;
    for (const auto &entry : filesystem::directory_iterator(path))
    {
        num_files++;
    }

    // Write the CSV column headers to the file
    dataset_file << "BeatmapID,";
    dataset_file << "Angle_0,Angle_1,Angle_2,Angle_3,";
    dataset_file << "Time_0,Time_1,Time_2,Time_3,";
    dataset_file << "Distance_0,Distance_1,Distance_2,Distance_3\n";

    // Parse each file in the distributions folder
    int i = 0;
    for (const auto &entry : filesystem::directory_iterator(path))
    {
        // Display the progress
        cout << "\r"
             << "Progress: " << i + 1 << "/" << num_files;

        // Open the file
        ifstream file(entry.path());
        if (file.is_open())
        {
            // Initialize the buckets
            vector<int> angle_buckets = {0, 0, 0, 0};
            vector<int> time_buckets = {0, 0, 0, 0};
            vector<int> distance_buckets = {0, 0, 0, 0};

            // Get each line of the file (each line is a transition between two (three for angle) notes)
            string line;
            while (getline(file, line))
            {
                // Skip empty lines
                if (line.empty())
                    continue;

                // Split the line by commas
                vector<string> split_line;
                stringstream ss(line);
                while (ss.good())
                {
                    string substr;
                    getline(ss, substr, ',');
                    split_line.push_back(substr);
                }

                // Parse the line into angle, time, and distance
                double angle = stod(split_line[0]);
                double time = stod(split_line[1]);
                double distance = stod(split_line[2]);

                // Increment the appropriate bucket
                if (angle < angle_bucket_bounds[0])
                {
                    angle_buckets[0]++;
                }
                else if (angle < angle_bucket_bounds[1])
                {
                    angle_buckets[1]++;
                }
                else if (angle < angle_bucket_bounds[2])
                {
                    angle_buckets[2]++;
                }
                else
                {
                    angle_buckets[3]++;
                }
                if (time < time_bucket_bounds[0])
                {
                    time_buckets[0]++;
                }
                else if (time < time_bucket_bounds[1])
                {
                    time_buckets[1]++;
                }
                else if (time < time_bucket_bounds[2])
                {
                    time_buckets[2]++;
                }
                else
                {
                    time_buckets[3]++;
                }
                if (distance < distance_bucket_bounds[0])
                {
                    distance_buckets[0]++;
                }
                else if (distance < distance_bucket_bounds[1])
                {
                    distance_buckets[1]++;
                }
                else if (distance < distance_bucket_bounds[2])
                {
                    distance_buckets[2]++;
                }
                else
                {
                    distance_buckets[3]++;
                }
            }

            // Close the input file
            file.close();

            // Get the total counts of each feature
            int angle_total = angle_buckets[0] + angle_buckets[1] + angle_buckets[2] + angle_buckets[3];
            int time_total = time_buckets[0] + time_buckets[1] + time_buckets[2] + time_buckets[3];
            int distance_total = distance_buckets[0] + distance_buckets[1] + distance_buckets[2] + distance_buckets[3];

            // Initialize the proportions
            vector<double> angle_props = {0.0, 0.0, 0.0, 0.0};
            vector<double> time_props = {0.0, 0.0, 0.0, 0.0};
            vector<double> distance_props = {0.0, 0.0, 0.0, 0.0};

            // Calculate the proportions for each bucket (normalize to 0-1)
            for (int i = 0; i < 4; i++)
            {
                angle_props[i] = (double)angle_buckets[i] / angle_total;
                time_props[i] = (double)time_buckets[i] / time_total;
                distance_props[i] = (double)distance_buckets[i] / distance_total;
            }

            // Write the beatmap ID to the CSV file
            dataset_file << entry.path().stem() << ",";
            // Write the angle, time, and distance proportions to the CSV file
            for (int i = 0; i < 4; i++)
            {
                dataset_file << angle_props[i] << ",";
            }
            for (int i = 0; i < 4; i++)
            {
                dataset_file << time_props[i] << ",";
            }
            for (int i = 0; i < 4; i++)
            {
                if (i == 3)
                    dataset_file << distance_props[i] << "\n";
                else
                    dataset_file << distance_props[i] << ",";
            }
        }
        // Error if the file cannot be opened
        else
        {
            printf("Unable to open file\n");
        }
        i++;
    }

    // Close the output file and return
    dataset_file.close();
    return 0;
}
