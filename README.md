# Statuspage

A statuspage generator and updater that lets you host your statuspage for free by Github. Uses 
issues to display incidents and labels for severity.

## Before you start

You'll need to create an GitHub API token. Go to your personal settings page on GitHub and locate 
the `Personal access tokens` tab on the left. Click on `Generate new token` and give it a description. Make
sure to check the `public_repo` scope. Copy the token somewhere safe, you won't be able to see it
again once you leave the page.

## Installation

   pip install statuspage

## Create a status page

To create a new status page, run

   statuspage create --token=<yourtoken>
   Name: mystatuspage
   Systems, eg (Website,API): Website, CDN, API
    
You'll be prompted for the name and the systems you want to show a status for. 

   - Name: This will be the name of the github repo where your status page is hosted. It will 
   create a new GitHub repo on your account with that name, so make sure you don't use something 
   that already exists.
   - Systems: The systems you want to show a status for. This can be your website, your API, your
   CDN or whatever else you are using.


The command takes a couple of seconds to run. Once ready, it will output the URLs to the issue tracker
and your new status page

   Create new issues at https://github.com/<login>/mystatuspage/issues
   Visit your new status page at https://<login>.github.com/mystatuspage/
   
## Create an issue

To create a new issue, go to your newly created repo and click on `New Issue`.

Click on the cog icon at labels on the right. What labels you choose next will tell the generator 
about the affected system(s) and the severity. Your system's labels are all black.

Add a systems label, eg. `Website` and pick a severity eg. `major outage` and add them to the issue.

Now, fill in the title, leave a comment and click on `Submit new issue`.

Go back to your commandline and type:

   statuspage update --token=<yourtoken>
   Name: mystatuspage

This will update your status page and show a *major outage* on your *Website*.

If you change the issue (eg. when you add a new label, create a comment or close the issue), you'll
need to run `statuspage update` again.


## Customizing

**Important:** All customizations have to happen in the `gh-pages` branch. If you are using the
command line, make sure to

    git checkout gh-pages
    
or, on the website, select the `gh-pages` branch before editing things.


### Logo

Just add a `logo.png` to the root directory.

### CSS

CSS is located at `styles.css` in the root directory. Just edit it and commit the file.