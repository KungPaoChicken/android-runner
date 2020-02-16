# Contributing to the Android Runner Framework
---

Thank you for your interest in helping enhance the Android Runner framework.  Our goal is to make energy consumption research on Android mobile devices more accessible and robust.  Using the framework saves time and provides several plugins for a range of metrics.  But unlike the Big Bang, the framework didn't arrive at its current state all at once; many students and researchers contributed to the code base in iterative steps. Important things to review before contributing: forking, branching, commit messages, plugintest and [pytest](https://docs.pytest.org/en/latest/).  There several projects in the works and several more that have yet to start.  More information on this can be found at the bottom.

## Before You Begin
It's important for us to make sure that any updates to the framework add value and that the updates adhere to the original goals of the framework.  Before spending a lot of time making substantial changes, please raise an `issue` on Github so we're made aware of the changes you'd like to implement.  We'll provide feedback to inform you whether we think it's viable.

## How to Begin
Whether you want to add a feature or clear away a bug, the first thing you should do is fork. Forking is like cloning, but any changes you want to incorporate to the parent repository must be reviewed via a pull request.  The easiest way to fork is to click on the fork option in the upper right hand corner on Github.  Next, clone your fork to your computer.  Before submitting a pull request, it is recommended to make sure your environment is ready to make a pull request.

## Environment
Your forked repository will come with one branch, called `master`.  Initially, it'll point to `master/origin`, which is your forked repository on Github.  Ideally, you'll want to be able to pull in updates from the parent repository into your forked repository.  To make your master points to the parent master, use the command line and type `git remote add --track master upstream git://github.com/S2-group/android-runner.git`.  To update your forked repo with parent repo, type `git fetch upstream` followed by `git merge upstream/master`.  In other words, don't directly change anything on your master branch. It should be used as a proxy to the master branch in the parent repository.

For changes and pull requests, create a second branch.  Any changes that need to be made after submitting a pull request should be made on a third branch to avoid polluting your pull request.

## Making Changes to Your Forked Repo
### Commits
Any commits should contain logically similar changes.  Combining a bug fix and a feature addition in the same commit is frowned on.  Commit messages (`git commit -m "[text]"`) should be informative but also concise.  Good commits make changes easier to review later.

### Plugins
If you're editing an existing plugin or adding a new one, there's an automated test called plugintest in examples/ that will ensure the plugin adheres to the requirements of the framework.  To   execute it, type: `python android-runner android-runner/examples/plugintest/config.json`.

## Before Submitting a Pull Request
When a pull request is submitted, a number of automated tests are performed on the TravisCI platform.  For an expedited review process, it's recommended to execute these tests in your local environment before submitting a pull request.  You can execute these tests in the android-runner directory with: `py.test [options] tests/unit`. It's also possible to run py.test with a specific module in tests/unit/. [Pdb](https://docs.python.org/3/library/pdb.html) is a good library to import if you experience issues that may be hard to resolve with print statements.  Don't forget to remove any debugging statements.

## Communication 
The best way to communicate with the Android Runner team is by raising an `issue` on Github.

## Projects
### In the Works
1. Monsoon Power Monitor plugin.

### Yet to be Assigned
