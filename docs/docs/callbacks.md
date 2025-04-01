
# Callbacks

Callbacks are a key part of the Threat Patrols Actions framework since they make it possible to 
emit results from an Action to other systems and processes. 

Callbacks are defined in the `callbacks` section of an Action YAML formated configuration file. 

## threatpatrols
Example `threatpatrols` callback configuration.

* Notice the ability to use environment variable values using `${}` variable name notation.

```yaml
threatpatrols:
  
  threatpatrols01example:
    api_key: "${TPASDEV_THREATPATROLS_APIKEY}"
```

## http
Example `http` callback configurations.

* Notice the ability to use tag values by referencing them as per `{tag.action_name}` all Action responses automatically-created tags and user-defined tags that can be referenced here.

```yaml
http:
  
  http01example:
    method: POST
    url: "https://httpbin.org/anything/test-example-post"
    headers:
      Authentication: "Bearer ${TPASDEV_FAUX_BEARER_TOKEN}"
    verify: false
    send: summary
    
  http02example:
    method: GET
    url: "https://httpbin.org/anything/test-example-get/?action-name={tag.action_name}&call-id={tag.call_id}"
```

## s3put
Example s3put callback configurations.

* Notice the special `call_id_prefix` that represents the year-month-day (in YYYYMMDD format) of the `call_id` value.
* Notice the various send types
    * `summary` summary data from the Action
    * `output` output from the Action
    * `input` input value that went into the Action
    * `content_b64decode` binary output from the Action base64 decoded from content.

```yaml
s3put:
  
  s3put01example:
    url: "s3://customer-bucket/testing/{tag.action_name}/{tag.call_id_prefix}/{tag.call_id}.summary"
    send: summary
    
  s3put02example:
    url: "s3://other-customer-bucket/testing/{tag.action_name}/{tag.call_id_prefix}/{tag.call_id}.out"
    send: output
    
  s3put03example:
    url: "s3://${TPASDEV_S3PUT_BUCKET}/testing/{tag.action_name}/{tag.call_id_prefix}/{tag.call_id}.in"
    send: input
    
  s3put04example:
    url: "s3://${TPASDEV_S3PUT_BUCKET}/testing/{tag.action_name}/{tag.call_id_prefix}/{tag.call_id}.content"
    send: content_b64decode
```

## slack
Example slack callback configurations

* Notice the use of send `content_b64decode` that sends a binary file/image/etc to the Slack channel with a message.

```yaml
slack:
  
  slack01example:  # send content_b64decode
    token: "${TPASDEV_SLACK_BOT_TOKEN}"
    channel: "${TPASDEV_SLACK_CHANNEL}"
    message: |
      *{tag.action_title}*
       - *url*: `{url}`
       - *status_code*: {status_code}
       - *nodename*: {tag.platform_node}
       - *call_id*: {tag.call_id}
       - *task_id*: {tag.task_id}
    send: content_b64decode

  slack02example:  # send summary
    token: "${TPASDEV_SLACK_BOT_TOKEN}"
    channel: "${TPASDEV_SLACK_CHANNEL}"
    message: |
      *{tag.action_title}*
       - *url*: `{url}`
       - *status_code*: {status_code}
       - *nodename*: {tag.platform_node}
       - *call_id*: {tag.call_id}
       - *task_id*: {tag.task_id}
    send: summary
```

## smtp
Example smtp callback configurations

* Notice the use of send `content_b64decode` that attaches a binary file/image/etc to the email to be sent.

```yaml
smtp:
  
  smtp01example:  # send content_b64decode
    smtp_host: "${TPASDEV_SMTP_HOST}"
    smtp_port: "${TPASDEV_SMTP_PORT}"
    smtp_user: "${TPASDEV_SMTP_USER}"
    smtp_pass: "${TPASDEV_SMTP_PASS}"
    email_to: "${TPASDEV_SMTP_EMAIL_TO}"
    email_from: "{tag.action_title} Testing <user@testing.null>"
    email_subject: "{tag.action_name} | call: {tag.call_id}"
    email_text: |
      {tag.action_title}
       - url: {url}
       - status_code: {status_code}
       - nodename: {tag.platform_node}
       - call_id: {tag.call_id}
       - task_id: {tag.task_id}
    send: content_b64decode

  smtp02example:  # send summary
    smtp_host: "${TPASDEV_SMTP_HOST}"
    smtp_port: "${TPASDEV_SMTP_PORT}"
    smtp_user: "${TPASDEV_SMTP_USER}"
    smtp_pass: "${TPASDEV_SMTP_PASS}"
    email_to: "${TPASDEV_SMTP_EMAIL_TO}"
    email_from: "{tag.action_title} Testing <user@testing.null>"
    email_subject: "{tag.action_name} | call: {tag.call_id}"
    email_text: |
      {tag.action_title}
       - url: {url}
       - status_code: {status_code}
       - nodename: {tag.platform_node}
       - call_id: {tag.call_id}
       - task_id: {tag.task_id}
    send: summary
```
