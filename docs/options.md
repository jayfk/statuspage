# Options

## Create a private status page

*Please note: Your Github API token needs the `repo` scope.*

To create a private status page, set the `--private` flag.

    statuspage create --private --token=<token>
    
This will create a private repository, however the GitHub page will be public.

## Use Organization Account

*Please note: You need to have the proper permissions to create a new repository for the given
organization.*

In order to create/update a status page for an organization, add the name of the organization to 
 the `--org` flag, e.g.:
 
     statuspage create --org=my-org --name=..
     
