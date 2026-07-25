# Quickstart for GitHub Actions

Try out the core features of GitHub Actions in minutes.

## Introduction

GitHub Actions is a continuous integration and continuous delivery platform that allows you to automate your build, test, and deployment pipeline. You can create workflows that run tests whenever you push a change to your repository, or that deploy merged pull requests to production.

This quickstart shows you how to use the GitHub user interface to add a workflow that demonstrates essential GitHub Actions features.

## Using workflow templates

GitHub provides preconfigured workflow templates that you can use as-is or customize. GitHub analyzes your code and suggests templates that might be useful. For example, if your repository contains Node.js code, you'll see suggestions for Node.js projects.

Templates cover:
- Continuous Integration workflows
- Deployment workflows
- Automation workflows
- Code Scanning workflows
- Pages workflows

You can browse the full list in the actions/starter-workflows repository.

## Prerequisites

- Basic knowledge of GitHub
- A repository on GitHub where you can add files
- Access to GitHub Actions

If the Actions tab is not displayed under your repository name, Actions may be disabled for the repository.

## Creating your first workflow

Create a workflow file called github-actions-demo.yml in the .github/workflows directory.

- If the directory exists: navigate to it, click Add file, then Create new file.
- If it does not exist: create the file as .github/workflows/github-actions-demo.yml from the main repository page.

GitHub discovers workflows only when they are saved in .github/workflows. The file must use .yml or .yaml.

## Example workflow contents

name: GitHub Actions Demo
run-name: ${{ github.actor }} is testing out GitHub Actions
on: [push]
jobs:
  Explore-GitHub-Actions:
    runs-on: ubuntu-latest
    steps:
      - run: echo "The job was automatically triggered by a ${{ github.event_name }} event."
      - run: echo "This job is now running on a ${{ runner.os }} server hosted by GitHub!"
      - run: echo "The name of your branch is ${{ github.ref }} and your repository is ${{ github.repository }}."
      - name: Check out repository code
        uses: actions/checkout@v6
      - run: echo "The ${{ github.repository }} repository has been cloned to the runner."
      - run: echo "The workflow is now ready to test your code on the runner."
      - name: List files in the repository
        run: |
          ls ${{ github.workspace }}
      - run: echo "This job's status is ${{ job.status }}."

## Viewing your workflow results

- Navigate to your repository on GitHub.
- Click Actions.
- Select the workflow from the left sidebar.
- Click the run name.
- Under Jobs, click the job name to expand its steps.

## Next steps

- Using workflow templates
- Building and testing your code
- Publishing packages
- Deploying to third-party platforms
- Managing your work with GitHub Actions
- Choosing what your workflow does
