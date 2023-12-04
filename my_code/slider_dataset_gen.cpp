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
    // Path to beatmap slider distribution folder
    string path = "B:\\Projects\\osu-sim\\sliders";

    // Bucket bounds for each feature
    vector<double> slider_length_bucket_bounds = {53.0, 123.0, 235.0};
    vector<double> slider_velocity_bucket_bounds = {0.0, 12.0, 46.0};

    // Create an output CSV file
    ofstream dataset_file;
    dataset_file.open("dataset_slider.csv");

    // Get the number of files in the directory
    int num_files = 0;
    for (const auto &entry : filesystem::directory_iterator(path))
    {
        num_files++;
    }

    // Write the CSV column headers to the file
    dataset_file << "BeatmapID,";
    dataset_file << "SRatio,";
    dataset_file << "SLength_0,SLength_1,SLength_2,SLength_3,";
    dataset_file << "SVelocity_0,SVelocity_1,SVelocity_2,SVelocity_3\n";

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
            vector<int> slider_length_buckets = {0, 0, 0, 0};
            vector<int> slider_velocity_buckets = {0, 0, 0, 0};

            // Write the beatmap ID to the CSV file
            dataset_file << entry.path().stem() << ",";

            // Get each line of the file (each line is a slider object)
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

                // If only one value is present, it is the slider-to-circle ratio of the beatmap
                if (split_line.size() != 2)
                {
                    dataset_file << stod(line) << ",";
                    continue;
                }

                // Parse the line into slider length and velocity if there are two values present
                double slider_length = stod(split_line[0]);
                double slider_velocity = stod(split_line[1]);

                // Increment the appropriate bucket
                if (slider_length < slider_length_bucket_bounds[0])
                {
                    slider_length_buckets[0]++;
                }
                else if (slider_length < slider_length_bucket_bounds[1])
                {
                    slider_length_buckets[1]++;
                }
                else if (slider_length < slider_length_bucket_bounds[2])
                {
                    slider_length_buckets[2]++;
                }
                else
                {
                    slider_length_buckets[3]++;
                }
                if (slider_velocity < slider_velocity_bucket_bounds[0])
                {
                    slider_velocity_buckets[0]++;
                }
                else if (slider_velocity < slider_velocity_bucket_bounds[1])
                {
                    slider_velocity_buckets[1]++;
                }
                else if (slider_velocity < slider_velocity_bucket_bounds[2])
                {
                    slider_velocity_buckets[2]++;
                }
                else
                {
                    slider_velocity_buckets[3]++;
                }
            }

            // Close the input file
            file.close();

            // Get the total counts of each feature
            int slider_length_total = slider_length_buckets[0] + slider_length_buckets[1] + slider_length_buckets[2] + slider_length_buckets[3];
            int slider_velocity_total = slider_velocity_buckets[0] + slider_velocity_buckets[1] + slider_velocity_buckets[2] + slider_velocity_buckets[3];

            // Initialize the proportions
            vector<double> slider_length_props = {0.0, 0.0, 0.0, 0.0};
            vector<double> slider_velocity_props = {0.0, 0.0, 0.0, 0.0};

            // Calculate the proportions for each bucket (normalize to 0-1)
            for (int i = 0; i < 4; i++)
            {
                if (slider_length_total != 0)
                    slider_length_props[i] = (double)slider_length_buckets[i] / slider_length_total;
                if (slider_velocity_total != 0)
                    slider_velocity_props[i] = (double)slider_velocity_buckets[i] / slider_velocity_total;
            }

            // Write the slider length and velocity proportions to the CSV file
            for (int i = 0; i < 4; i++)
            {
                dataset_file << slider_length_props[i] << ",";
            }
            for (int i = 0; i < 4; i++)
            {
                if (i == 3)
                    dataset_file << slider_velocity_props[i] << "\n";
                else
                    dataset_file << slider_velocity_props[i] << ",";
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
