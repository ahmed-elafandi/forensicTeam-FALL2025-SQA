1. Activities Completed

For this assignment, we wrote a fuzzing script that generates random inputs and runs them through the MLForensics functions. The script captures all errors and records them in a crash log file. We also added logging statements to the main code so the program records when functions start, what they receive, and when exceptions occur.

We created a GitHub Actions workflow that installs Python, installs the necessary libraries, and runs the fuzzing script automatically on every push. The workflow also prints the crash log if any crashes happen. During setup, we fixed issues such as missing imports, incorrect file paths, and indentation errors until the CI pipeline ran successfully.

2. Lessons Learned

We learned that fuzzing can quickly expose unexpected bugs that normal testing might miss. Adding logging made it easier to understand what the program was doing and why it failed. Setting up continuous integration showed how important it is to have clean paths, correct dependencies, and consistent environments. We also learned how even small errors, like a wrong directory name or missing module, can cause the workflow to fail.

3. Final Status

The fuzzing script, logging updates, and CI workflow are all working. The project now automatically runs the fuzzing script through GitHub Actions and reports any crashes.
