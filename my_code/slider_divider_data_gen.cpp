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
    // For each file in the sliders folder, print the file name
    string path = "B:\\Projects\\osu-sim\\sliders";

    // Create an output file for slider lengths
    ofstream slider_lengths_file;
    slider_lengths_file.open("slider_length.txt");

    // Create an output file for slider velocities
    ofstream slider_velocities_file;
    slider_velocities_file.open("slider_velocity.txt");

    // Get the number of total files in the directory
    int num_files = 0;
    for (const auto & entry : filesystem::directory_iterator(path)) {
        num_files++;
    }
    int i = 0;
    for (const auto & entry : filesystem::directory_iterator(path)) {
        // Print the progress.
        printf("Progress: %d/%d: ", i+1, num_files);
        ifstream file(entry.path());
        if (file.is_open()) {
            // Print the file name
            cout << entry.path().filename() << endl;
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
                // If split line does not have 2 elements, skip it
                if (split_line.size() != 2)
                    continue;
                // Write the first element to slider_lengths.txt
                slider_lengths_file << split_line[0] << "\n";
                // Write the second element to slider_velocities.txt
                slider_velocities_file << split_line[1] << "\n";
            }
            file.close();
        } else {
            printf("Unable to open file\n");
        }
        i++;
    }
    slider_lengths_file.close();
    slider_velocities_file.close();
    return 0;
}
