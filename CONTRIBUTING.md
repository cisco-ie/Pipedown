Contributing
============

Contributions are welcome!

**Please carefully read this page to make the code review process go as smoothly as possible and to maximize the likelihood of your contribution being merged.**

## License Agreement

Pipedown is licensed under the [Apache-2 license](https://www.apache.org/licenses/LICENSE-2.0). In your commit messages, you must specify that you agree to contribute under the Apache license. Pull requests also must agree to submit under the Apache license. 

## Bug Reports

For bug reports or requests [submit an issue](https://github.com/cisco-ie/Pipedown/issues).

## Pull Requests

The preferred way to contribute is to fork the [main repository](https://github.com/cisco-ie/Pipedown) on GitHub.

1. Fork the [main repository](https://github.com/cisco-ie/Pipedown).  Click on the 'Fork' button near the top of the page.  This creates a copy of the code under your account on the GitHub server.

2. Clone this copy to your local disk:

        $ git clone https://github.com/cisco-ie/Pipedown
        $ cd Pipedown

3. Create a branch to hold your changes and start making changes. Don't work in the `master` branch! If you are adding a feature, use the format 'feature/my-feature', for a bug use 'bug/issue-id'.

        $ git checkout -b feature/my-feature

4. Work on this copy on your computer using Git to do the version control. When you're done editing, run the following to record your changes in Git:

        $ git add modified_files
        $ git commit

5. Push your changes to GitHub with:

        $ git push -u origin my-feature

6. Finally, go to the web page of your fork of the `Pipedown` repo and click 'Pull Request' to send your changes for review.

### GitHub Pull Requests Docs

If you are not familiar with pull requests, review the [pull request docs](https://help.github.com/articles/using-pull-requests/).

### Code Quality

Ensure your pull request satisfies all of the following, where applicable:

* Follows [PEP 8](http://legacy.python.org/dev/peps/pep-0008/) code quality standards, as well as [PEP 257](https://www.python.org/dev/peps/pep-0257/) for docstrings.

* Is thoroughly unit-tested. 
