function postData(tech_family_id, environment, value) {

  var data = {
    'value': value,
    'environment': environment,
    'tech_family_id': tech_family_id
  };
  var user = ""
  var password = ""

  var headers = {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": "Basic "+ Utilities.base64Encode(user+":"+password)
  };

  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data),
    "headers" : headers
  };

  try {
    UrlFetchApp.fetch('https://cost-management-system-appscript.moladin.com/api/gcp/index-weight', options);
  }
  catch (e) {
    sendAlert("Production", data, e)
  }

  try {
    UrlFetchApp.fetch('https://cost-management.moladin.com/api/gcp/index-weight', options);
  }
  catch (e) {
    // sendAlert("Development", data, e)
  }
}

function getMOFIndexWeight() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Bobot MFI");

  var techFamId = [3, 2, 1]
  var env = ["development", "staging", "production"]

  for (let tf = 0; tf < 3; tf++ ) {
    for (let e = 0; e <3; e++){
      cell = sheet.getRange(17+tf, 6+e )
      value = cell.getValue()
      tech_family_id = techFamId[tf]
      environment = env[e]
      postData(tech_family_id, environment, (value * 100).toFixed(2))
    }
  }
}

function slackPayload(env, payload, errMessage) {
  var today = new Date();
  var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
  var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
  var dateTime = date+' '+time;

  return {
    "username": `AppScript ${env} Notification`,
    "icon_emoji": ":rotating_light:",
    "channel": "#moladin-finops-alert",
    "attachments": [
		{
      "color": "#c40000",
			"blocks": [
				{
					"type": "header",
					"text": {
						"type": "plain_text",
						"text": "IndexWeight Sync ERROR from AppScript!",
						"emoji": true
					}
				},
				{
					"type": "divider"
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": "@here, Synchronization Failed. AppScript encountered an issue while syncing data with our system."
					}
				},
				{
					"type": "divider"
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": `Time: *${dateTime}*`
					}
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": `Environment: *${env}*`
					}
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": "Payload: ```" + JSON.stringify(payload) + "```"
					}
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": "Message:\n ```" + errMessage + "```"
					}
				},
				{
					"type": "divider"
				},
				{
					"type": "actions",
					"elements": [
						{
							"type": "button",
							"text": {
								"type": "plain_text",
								"text": "Google AppScript",
								"emoji": true
							},
							"value": "appscript",
							"url": "https://script.google.com/u/1/home/projects/1JKL1Ka_upXRjpQT69v3CqafIhPbbX5reXykTsrD-3fp47K4ftmjBhedq"
						}
					]
				},
				{
					"type": "actions",
					"elements": [
						{
							"type": "button",
							"text": {
								"type": "plain_text",
								"text": "Living Document",
								"emoji": true
							},
							"value": "livdoc",
							"url": "https://docs.google.com/spreadsheets/d/1L9XDJa4yDsSSEy26RwbNQEOFvvf6t43VuC74VRZctkA/edit#gid=369531361"
						}
					]
				}
			]
		}
	]
  }
}

function sendAlert(env, payload, errMessage) {

  var data = slackPayload(env, payload, errMessage)

  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data)
  };

  try {
    UrlFetchApp.fetch('https://hooks.slack.com/services/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', options);
  }
  catch (e) {
    console.log(e)
  }
}

function getMDIIndexWeight() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Bobot MDI");

  // dana_tunai & platform
  var techFamId = [6, 9, 5]
  var env = ["development", "staging", "production"]

  for (let tf = 0; tf < 3; tf++ ) {
    for (let e = 0; e <3; e++){
      cell = sheet.getRange(9+tf, 6+e )
      value = cell.getValue()
      tech_family_id = techFamId[tf]
      environment = env[e]
      postData(tech_family_id, environment, (value * 100).toFixed(2))
    }
  }
  debugger;
}

function sync() {
  getMOFIndexWeight()
  getMDIIndexWeight()
}