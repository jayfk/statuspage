## Customizing

**Important:** All customizations have to happen in the `gh-pages` branch. If you are using the
command line, make sure to

    git checkout gh-pages
    
or, on the website, select the `gh-pages` branch before editing things.

### Template

The template is fully customizable, edit `template.html`.

### Logo

Add a `logo.png` to your repo's root and change `template.html` to point to that file.

### CSS

CSS is located at `style.css` in the root directory. Just edit it and commit the file.

### Use a subdomain

If you want to use your own domain to host your status page, you'll need to create a CNAME file
in your repository and set up a CNAME record pointing to that page with your DNS provider.

If you have e.g. the domain `mydomain.com`, your GitHub username is `myusername` and you want 
your status page to be reachable at `status.mydomain.com`


- Create a `CNAME` file in the root of your repository

        status.mydomain.com
    
- Go to your DNS provider and create a new CNAME record pointing to your

  
          Name     Type      Value 
          status   CNAME     myusername.github.io

See [Using a custom domain with GitHub Pages](https://help.github.com/articles/using-a-custom-domain-with-github-pages/) 
for more info.