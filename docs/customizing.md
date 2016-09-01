## Customizing

**Important:** All customizations have to happen in the `gh-pages` branch. If you are using the
command line, make sure to

    git checkout gh-pages
    
or, on the website, select the `gh-pages` branch before editing things.

### Template

Don't edit the `template.html` file directly, as it will change with each upgrade.

Instead, create a file called `config.json` in the root of your repository and change the defaults. Don't forget to run `statuspage update` afterwards.

```javascript
{
    "footer": "Status page hosted by GitHub, generated with <a href='https://github.com/jayfk/statuspage'>jayfk/statuspage</a>",
    "logo": "https://raw.githubusercontent.com/jayfk/statuspage/master/template/logo.png",
    "title": "Status",
    "favicon": "https://raw.githubusercontent.com/jayfk/statuspage/master/template/favicon.png"
}
```

Please note: `config.json` has to be valid JSON. The best way to validate it online is at [jsonlint.com](http://jsonlint.com/).

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