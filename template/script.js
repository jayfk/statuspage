var l = function (string) {
    return string.toLocaleString();
};

var systemLabelColor = "171717";
var severityLabels = {
    "1192FC": "investigating",
    "FFA500": "degraded performance",
    "FF4D4D": "major outage"
};

function render() {

    var endpoints = {
        "issues": "https://api.github.com/repos/" + config.repo + "/issues?state=all&sort=created&direction=desc",
        "labels": "https://api.github.com/repos/" + config.repo + "/labels"
    };

    // show an indicator that we are doing something
    $("#load-indicator").show();

    var labels = request(endpoints.labels, render);
    if (labels == undefined) {
        return
    }

    var issues = request(endpoints.issues, render);
    if (issues == undefined) {
        return
    }

    var systems = [];

    labels.forEach(function (label) {
        if (label.color == systemLabelColor) {
            systems.push({"name": label.name, "status": "operational"});
        }
    });

    systems = systems.sort(function(a, b){
       return a.name.localeCompare(b.name);
    });

    var incidents = [];
    var incidentCount = 0;
    issues.every(function (issue) {
        issue.severity = "";
        issue.affectedSystems = [];
        issue.updates = [];
        issue.created_at = new Date(issue.created_at);
        issue.labels.forEach(function (label) {
            if (severityLabels[label.color] != undefined) {
                issue.severity = severityLabels[label.color];
            } else if (label.color == systemLabelColor) {
                issue.affectedSystems.push(label.name);
            }
        });

        // make sure that the isse has
        if(issue.affectedSystems.length > 0 && // a system label
            issue.severity != undefined && // a severity label
            issue.user.login.indexOf(config.collaborators) != -1 // is created by a collaborator
        ){

            if (issue.state == "open") {
                issue.affectedSystems.forEach(function (affectedSystem) {
                    systems.forEach(function(system){
                       if(system.name == affectedSystem){
                           system.status = issue.severity;
                       }
                    });
                });
            }else{
                issue.severity = "resolved";
            }

            incidents.push(issue);
        }

        // limit displayed incidents to 10
        if(incidentCount++ == 10){
            return false;
        }
        return true;
    });

    // populate the panels
    var panels = [];
    systems.forEach(function(system){
       if(system.status != "operational"){
           var hasPanel = false;
           panels.forEach(function(panel){
               if(panel.status == system.status){
                   hasPanel = true;
                   panel.systems.push(system.name);
               }
           });
           if(!hasPanel){
               panels.push({"status": system.status, "systems": [system.name]})
           }
       }
    });

    // render the template
    var template = $('#template').html();
    Mustache.parse(template);
    var rendered = Mustache.render(template, {"systems": systems, "incidents": incidents, "panels": panels});
    $(main).html(rendered);

    setTimeout(function(){$("#load-indicator").hide()}, 1000);
}

function request(endpoint, callback) {

    callback = callback || false;
    var cached = Lockr.get(endpoint);
    $.ajax({
        url: endpoint,
        beforeSend: function (request) {
            if (cached != null && cached.etag != null) {
                request.setRequestHeader("If-None-Match", cached.etag);
            }
        },

        success: function (data, textStatus, request) {
            console.log(request.getResponseHeader('X-RateLimit-Remaining'));
            if (request.status == 304) {

            } else {
                Lockr.set(endpoint, {"data": data, "etag": request.getResponseHeader('ETag')});
                if (callback) {
                    callback();
                }
            }
        },
        error: function (request, textStatus, errorThrown) {
            console.log(request.getResponseHeader('X-RateLimit-Remaining'));
        }
    });
    return (cached) ? cached.data : undefined;
}