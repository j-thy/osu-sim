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
    // Path to slider distributions folder
    string path = "B:\\Projects\\osu-sim\\sliders";

    // Create an output file for slider lengths and velocities
    ofstream slider_lengths_file;
    slider_lengths_file.open("slider_length.txt");
    ofstream slider_velocities_file;
    slider_velocities_file.open("slider_velocity.txt");

    // Get the number of files in the directory
    int num_files = 0;
    for (const auto &entry : filesystem::directory_iterator(path))
    {
        num_files++;
    }

    // Parse each file in the sliders folder
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

                // Skip the line with the slider-to-circle ratio
                if (split_line.size() != 2)
                    continue;
                    
                // Write the first element to slider_lengths.txt
                slider_lengths_file << split_line[0] << "\n";
                // Write the second element to slider_velocities.txt
                slider_velocities_file << split_line[1] << "\n";
            }
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
    slider_lengths_file.close();
    slider_velocities_file.close();
    return 0;
}
