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
    // For each file in the dist folder, print the file name
    string path = "B:\\Projects\\osu-sim\\dists";

    // Create an output file for angles
    ofstream angles_file;
    angles_file.open("angles.txt");

    // Create an output file for times
    ofstream times_file;
    times_file.open("times.txt");

    // Create an output file for distances
    ofstream distances_file;
    distances_file.open("distances.txt");

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
                // Write the first element to angles.txt
                angles_file << split_line[0] << "\n";
                // Write the second element to times.txt
                times_file << split_line[1] << "\n";
                // Write the third element to distances.txt
                distances_file << split_line[2] << "\n";
            }
            file.close();
        } else {
            printf("Unable to open file\n");
        }
        i++;
    }
    angles_file.close();
    times_file.close();
    distances_file.close();
    return 0;
}
