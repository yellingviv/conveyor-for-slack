# :sparkles: CONVEYOR FOR SLACK :sparkles:

### This is a friendly little Python app that will allow you to integrate your instance of Conveyor with your Slack workspace.

In order to make use of this, you will need an account with both [Conveyor](www.conveyorhq.com) and [Slack](www.slack.com). Conveyor does not have a dev portal, but for Slack you will need to use their [developer portal/API interface](api.slack.com).

I built this using Bolt for Python, so most of the Slack interactions are handled by built in shortcuts. I used Flask as my server to handle the requests, as Bolt's built in server is really just meant for local testing and basic http. Other than that, the libraries involved are fairly simple and straightforward--requests, json, logging, etc. You can load those into your virtualenv from the requirements.txt in this repo.

### This can do some basic but enjoyable things for you--
The main purpose of this tool is simply to push new room access requests into Slack, and allow people who are authorized Conveyor users to approve or reject those requests. This includes sourcing any special optional permissions group that you have, so different customers can be granted different permissions.

_POV, u r using conveyor-for-slack and it is rad:_
![image](https://user-images.githubusercontent.com/19272711/134429472-33736ea5-4726-44d4-bf19-111f352e40ef.png)
This is an example of what a room requests looks like when shared to Slack. It includes the email address of the person requesting, the timestamp, and whatever message they included with their request. The text at the top is a link to that specific request in Conveyor. Below, the privileges are pulled directly from the Conveyor API so that as our privileges change, so does the menu.

If you choose to accept the request, it is logged and the request goes through to the Conveyor API to be processed and the customer is granted access.

![image](https://user-images.githubusercontent.com/19272711/134429583-7c6ed968-6b6d-4c1a-b4ae-7715b169f409.png)
If you choose to hit reject, a modal will pop up requesting a note about why. We chose to implement this so that anyone can answer questions about why a request was rejected without having to track down the original responder. This is not optional and must be filled out for the response to go through. This can easily be removed by pulling out the modal step in the `@app.action("reject")` section.

![image](https://user-images.githubusercontent.com/19272711/134429696-42b484a9-deed-46ad-8433-77cfe617a9a9.png)
Once the request has been processed and a 200 has been received from Conveyor, the original message in Slack is updated to reflect that the request was either approved or rejected, who did it, and when. Where applicable, the note is included. This is intended for transparency and self-service so that sales reps can search the Conveyor request channel and see whether or not their customer has had their request taken care of and what the response was.

### To get this up and running,
you will need to:

* get your Conveyor API key from your integrations menu
* create a Slack app to install this to on your workspace in your Slack API apge
* get your Slack signing secret and bot token from the API page
* get your channel ID for where you want your app to post
* set up a server either locally or in your infra
* assign that URL to your Slack app in the interactions page
* update the .env file with your assorted secrets

From there, you can pretty much start the up and be good to go. For my deployment at my company, mine is in a Docker container on Nomad, with Consul and some other fun frippery providing commuication with the outside world. So everything is orchestrated and all needed aspects are launched in the Dockerfile.

If you're running a local server, such as [nginx](www.nginx.com), you'll need to start your nginx server on the correct port that you gave your Bolt/Flask app, and then run `python3 app.py` to launch the app.

I recommend going through and looking at some of the error messages. I had them custom tailored to me and my team, so when I changed them for mass consumption, they got a little sterile. Also, see if you want nearly as verbose of logging as I like to have.

### Please fork the hell out of this, but...
Also please be aware that I will probably not ever look at any submitted PRs to this repo. I wrote this for my company to make my colleagues' lives easier, and also because I thought it was fun. I'll be maintaining it, and likely adding more features, within my professional GitHub organization, but updates will be ported over here only infrequently. This isn't to be an ass, just honesty. I'm not gonna think about it, and I don't want to leave you hanging. However, the great folks at Conveyor didn't have an API when I first wanted to do this, and they were amazing about being willing to spin something up to see what could happen. I would really love to see more companies and devs using their API. Their team was so great to work with, and I hope you will enjoy working with this too!
