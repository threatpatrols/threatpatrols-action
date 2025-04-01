<a href="https://www.threatpatrols.com">
<img src="assets/img/threatpatrols-eyeprint-banner-black-344×90.png#only-light" style="height: 70px; float: right; margin-left: 24px; margin-bottom: 24px">
<img src="assets/img/threatpatrols-eyeprint-banner-white-344×90.png#only-dark" style="height: 70px; float: right; margin-left: 24px; margin-bottom: 24px">
</a>

# Threat Patrols Actions

Threat Patrols Actions (TPAS) are collections of well known security tools that have been packaged, 
wrapped and kept up-to-date in a way that makes their use in continuous security automation pipelines _much_ easier.

!!! warning "Attention"
    These docs relate to the Threat Patrols Action framework itself.   If you want a **big list** of 
    Threat Patrols Actions and their associated documentation, you can find them [over here](actions.md).

## Features
* :octicons-plug-24: all actions are available as ready-to-run **API** microservices.
* :octicons-terminal-24: all actions are available as **command-line** tools (within Docker containers).
* :fontawesome-brands-github: all actions can be invoked as **Github Actions**!
* :fontawesome-brands-square-gitlab:{ .gitlab } all actions can be invoked as **Gitlab Runner** templates!
* :octicons-zap-24: all actions can invoke multiple **callbacks** with payloads to send outputs to HTTP endpoints,
  :fontawesome-brands-aws: S3-compatible-storage, :fontawesome-brands-slack: Slack messages, :octicons-mail-24: SMTP 
  emails.
* :octicons-history-24: API actions can be invoked as **background** tasks with a `task_id` for back reference. 
* :fontawesome-solid-code: Outputs are **JSON** formatted making it easy to integrate with other systems, custom binary outputs are possible. 
* :octicons-heart-fill-24:{ .heart } All tools are **vetted**, **validated** and kept **up-to-date** by us for you.

This means you can do things like -

* Create **AI/LLM pipelines** to perform `nmap` scans and receive well formatted results to consume with your favorite AI model.
* Schedule regular `nmap` scans **inside your private network** using a local Github Runner, save the results to S3 
  and get a Slack message with results.
* Invoke `nmap` scans from your **n8n workflows** and receive results as callbacks then they finish.
* Refer back to previous `nmap` runs to recover results (from S3) for scans performed many months ago; awesome for 
  security assessments.

These are just some ordinary examples using plain-old `nmap`

Threat Patrols Actions has **many other** well-known security tools vetted, validated, packaged and ready to 
use, check them out [here](actions).


## Threat Patrols
Threat Patrols is an Australian cybersecurity company that provides continuous SecOps for organizations seeking 
additional cybersecurity capacity.  We develop and release our awesome tool-chains as well.  Find us [here](https://www.threatpatrols.com) if 
you'd like us to help manage your Threat Patrols Actions outputs and workflows.


## Apache 2.0 License
```text
Copyright 2025 Threat Patrols Pty Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
