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

    // Create an output file for angles, times, and distances
    ofstream angles_file;
    angles_file.open("angles.txt");
    ofstream times_file;
    times_file.open("times.txt");
    ofstream distances_file;
    distances_file.open("distances.txt");

    // Get the number of files in the directory
    int num_files = 0;
    for (const auto &entry : filesystem::directory_iterator(path))
    {
        num_files++;
    }

    // Parse each file in the distributions folder
    int i = 0;
    for (const auto &entry : filesystem::directory_iterator(path))
    {
        // Display the progress
        printf("Progress: %d/%d: ", i + 1, num_files);

        // Open the file
        ifstream file(entry.path());
        if (file.is_open())
        {
            // Print the filename as part of the progress
            cout << entry.path().filename() << endl;
    
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

                // Write the first element to angles.txt
                angles_file << split_line[0] << "\n";
                // Write the second element to times.txt
                times_file << split_line[1] << "\n";
                // Write the third element to distances.txt
                distances_file << split_line[2] << "\n";
            }

            // Close the input file
            file.close();
        }
        // Error if the file cannot be opened
        else
        {
            printf("Unable to open file\n");
        }
        i++;
    }

    // Close the output files and return
    angles_file.close();
    times_file.close();
    distances_file.close();
    return 0;
}
