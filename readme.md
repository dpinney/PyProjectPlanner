### PyProjectPlanner - What's It Do?

Give this Python script a list of tasks in a .csv, and it will spit out a .pdf with some timelines. Those will help you figure out how long your project will take, who is getting overworked, how much money you'll need to raise to keep your project going, etc.

I built this because I had to plan some projects at work and Excel was driving me crazy with its limited charting options and general slowness and buginess.

### Installation and Walkthrough

0. Install the requirements with `pip install matplotlib`.
1. Download [the scripts](blah).
2. In the script directory run `python PyProjectPlanner.py ./testTasksArtisinalSandwich.csv testOutputNew.pdf` to run the tests.
3. You'll have a new PDF with all the output. On page one, it shows all the tasks with areas proportional to how much money you're spending on them and arranged by start and end dates:
![Chart of budget by task.](https://raw.githubusercontent.com/dpinney/PyProjectPlanner/master/walkthroughScreenshotTasks.png)
4. On the second page of the output, you have the number of hours each person is working by year:
![Chart of hourly schedules per worker.](https://raw.githubusercontent.com/dpinney/PyProjectPlanner/master/walkthroughScreenshotSchedules.png)

### Bugs, Tests, etc.

This script works for me on Mac OS X with the default Python (2.7) and matplotlib installed via pip like its described in the walkthrough. Let me know in the issues if it doesn't work for you.