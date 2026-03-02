#incident #stripe/incident


- If I discover large scale issues (all apps are slowed or failing), open an incident
- Send out user communication to inform users about the incident and that we are investigating. If we already know a root case, also tell users that we are working on mitigating impact and will restart any failed jobs, and send updates once we know more.
- Check if error happens correlates with Zoolander deploy. Use splunk to check when the error starts. Use zoolander deploy board to check deploy finish time. Example: https://amp.corp.stripe.com/deploy/deploy1.northwest.stripe.io%2Fdeploy_kEf-Nh8sSAKFPiH-cvSnww
	- If confirmed, check if I have permission, or find someone who has permission to rollback the Zoolander deploy
	- Find the offending PR in this deploy and revert it. Merge revert so that Zoolander deploy can continue.
	- Confirm apps are launching successfully after revert
- Rerun failed jobs. 
	- Example command: `airflow clear_for_time_range -f -d -t '.*' -s '2023-05-10 21:00:00' -e '2023-05-10 22:35:00' -dx '.*'`
- Hand-off the incident PM role to the current oncall or self.
- Unlock zoolander deploy when ready
- Impact analysis
- Update the incident slack channel "SUMMARY" (maybe the incident reporter bot will do it automatically?)
- Advance incident status at the Slack incident channel using bot.
- Do not involve Habib when not necessary. He is a manager, and he may ask a lot of questions that would create a lot more work for me.

## Follow ups
- Should we add a dashboard to the team's weekly operations dashboard?
- AAR meeting.
	- Determine which team owns AAR?
	- Plan for longer meeting (45min or 1hr) if there are already contention.




# Past Examples

## ir-pink-paraphrase

- Dmitry: decide that we should roll back a bad PR.
- Dmitry: came up with a list of impacted tasks by querying splunk with the error message.
- Dmitry: noted in the channel that we should page another team because there is no comments in the PR.
- Dmitry: decided that we are not rolling back zoolander because impact is limited, by posting to the channel and referring another thread so everybody in the channel is on the same page.
- Dmitry: ask me (yichen) to drive RCA, so that he can focus on revert the bad PR.
- Habib: come up with a two sentence impact assessment and ask the impacted user to validate if it is accurate.
- Gaurav: regarding reverting bad PR, ask if we should bypass codeowners or page the code owners. I think it is more important to be explicit here instead of jumping into action.
- Dmitry: just an hour after asking me (yichen) to own RCA, he asked in the incident channel for updates: "Yi any news on RCA?"
- Gaurav: locked zoolander deploys to ensure that the revert is picked up before the next deploy.
- Gaurav: update the channel that the zoolander deploy is finished. The fix is in. Kicked off task to verify the fix. Note that he keeps the incident channel updated with what he is working on.
- Gaurav: update the channel that the incident is mitigated at this point. Declare the next step is to put proposal to advance soon.
- Gaurav: assigned incident report to A&A team. Ask if they think differently about this decision.
- Gaurav: take the ownership of the report because the other team won't take it, but follow up with them with updates.



## [pile-hexagon](http://go/ir/pile-hexagon?tab=remediations)
- Context: batcom is paged because of an important job is failing
- Habib: joined the incident channel after the runner is called.
- Dmitry: ask the user to share a link. 
- Dmitry: Compared two runs of this app (this is IC work)
- Dmitry: provided extra context and comment on a thread. IC work.
- Notably, this incident is R4,S3. There is not much involvement by Dmitry and Habib. 


## [notice-factor](https://incident-reporting.corp.stripe.com/wf/incidents/notice-factor)
- Zhen: updated the channel with each step. We migrated, we identified root cause, we rolled back, we verified the fix.
- Helen: we should disable 



  
## poised-ordinal
- Zhen called an incident because offending jobs are taking too much disk space.
- Zhen: suggest it is better to kill the job now and investigate inputsize.
- Vivek: report that data is still not in, (escalation), ask if need any help here?
- Vivek: escalade again: given this has been open >24 hours, does it make sense to increase R level, so we can have more teams to help on this?
- Zhen: update the channel that the incident is now mitigated.
- ilya: ask, can you help us understand why this issue is manifesting and what can be done about it. Then he continued asking the questions based on the response.
- Habib: ask Zhen to update the BRB and close the incident.


## [amplify-reach](https://incident-reporting.corp.stripe.com/wf/incidents/amplify-reach)
- Gaurav: recommend Vein to send out some comms to users to let them know that we are investigating these failures.
- Gaurav: update the channel that he is going to check if it corelates with zoolander deploy and roll it back if so. Note that I never did such updates in the incident channel. I just went ahead and do my thing instead of telling people what I am doing.
- Gaurav: have some question that he doesn't know, looping in a runner of a sister team. Got answer. 
- Vein: update the incident channel with his draft user comm for feedbacks.
- Gaurav: give feedback, and say that we will restart failed jobs after mitigating the impact.
- Gaurav: give further feedback to the user comm that we will update once we know more. Note this is what I should do if I don't have a clear answer. I
- Gaurav: ask Helen to verify that apps are launching successfully post rollback.
- Gaurav: ask  to run clear_for_timerange.
- Gaurav: ask Helen if it is OK to hand off incident PM role to her, and explain the remaining items are (1)  send out updated comms once the incident is mitigated, and (2) unlock zoolander once revert is ready to deploy.
- Helen: now as incident PM, reset the channel topic, and make her as incident PM (noted as part of incident channel topic)
- Helen: updated incident channel topic, with more accurate incident summary.
- Helen: created incident proposal


## ir-distance-tangible: RDP Express Data Archiver missed SLA
- Adam: ask the downstream user if they have a guess at the root cause. Any hint on whether this might happen again?
- Xuhui: believe this is a batcom issue. Included batcom runner maybe because it's only 5:40pm.
- Helen: announced that she is catching up.
- Helen: tell that she may have seen this before, and tell that she will check jira
- Dmitry: ask if there is any alive stuck task, he want to investigate because there is no progress so far.
- Dmitry: ask to do a zoom call to sync up.
- Dmitry: tell the incident channel that a few of us are doing RCA in the zoom call. By now this zoom is on for about one hour.
- Dmitry: update the channel again 30 minutes later, discovered that the app is using a long timeout value. Explained the 3 next steps. I suspect that Dmitry figured out these 3 next steps in the zoom call and update the channel. This is what I didn't do. I did the zoom call. I didn't update the channel to leave a trace of what I did.
- Dmitry: update the channel with new findings. Interestingly, the finding is that this is a dead-end and the clue he is after is expected, as he found a JIRA on YARN.
- Adam: tell the channel that he will schedule a seperate meeting with event enrichment to ensure they have a clearer understanding on impact and comes for the Data Archiver.
- Dmitry: ask if Yashiyah is looking at a certain issue from our end or anybody else. This is a way to commit Yashiyah or to close the loop.
- Dmitry: ask the user how bad it is on his end, and ask him to file a ticket if not urgent or open another incident if they will miss SLA or going to miss SLA.

## ir-[quench-optimist](https://incident-reporting.corp.stripe.com/wf/incidents/quench-optimist)
- Habib: ask the user could they move this app to their own queue? 


## ir-[dinner-current](https://incident-reporting.corp.stripe.com/wf/incidents/dinner-current)
- Gaurav: opened the incident for investigating silent data loss reported by Accounting team. In addition to opening the ticket, he provided the current knowledge, including (1) how often this has happened recently, (2) how frequently the app runs (hourly), (3) confirmed that the issue is not reproducible. Note that my first question when I heard about such incident is if it is reproducibile.
- Gaurav: tell the channel that the user team has manual script to fix it.
- Habib: ask if the user has a mitigation in place had this happen during the end of the UAR. The answer was yes. Then habib ask if that's sufficient to meet SLA. The answer is also yes.
- Dmitry: contributing by looking for clues in the job.  Ask Shahryar if he had a chance to audit operations on this directory which is where the data loss happens. Shahryar actually doesn't know how to do this. Dmitry says he doesn't know either, but the renames should be a good proxy for that.
- Dmitry: conclude that it is not hdfs file corruption, but it is silent data loss from user point of view.
- Dmitry, run this query in splunk: `"/tmp/hadoop_unknown_QjxRTuLm/tmp_data_94420" | dedup src | stats count by cmd`
- Gaurav: silently following the investigation thread (note that when people are obviously busy, no need to ask distracting questions), and then tell the thread that he found an error in the log that may be related.
- Gaurav: independently investigate, and tell the thread that he has more clue that is related, that delete command came from a different ip.
- Gaurav: updated the incident description to include a link to the google doc that tracks the current action items. This doc is named by the incident ID.
- Gaurav: tell the incident channel, thanks Dmitry and Shahryar and report we have a root case. Then he explained what is the RCA, the short term mitigation option, including three, and long term fix, is TBD. Note that he provided options even though they may be proven wrong at a later time. Also note that it is OK to have an unknown long term fix. The point is that he updated the channel with the current state.
- Dmitry: ask the impacted user how tight their SLAs are for this app.
- Dmitry: opened a new thread to figure out patterns of other apps that might be impacted. 
	- Dmitry: update the thread with the query based on his heuristics. Note that I came up with a query but I didn't paste the query to the slack. 
	- It's about 9pm
- Gaurav: updated the channel with what Dmitry found from a thread in the channel. Looks like Gaurav is pretty good at communication and ensure that no lose thread was lost.


## ir-[pink-paraphrase](https://incident-reporting.corp.stripe.com/wf/incidents/pink-paraphrase)
- Gaurav: arrived the channel early, so he add some context. Link to related slack threads from other channels. This is to keep everybody updated with the context and how this incident correlates to other incidents.
- Dmitry: after Helen discovered the related PR, he suggested that we should roll it back. and asked "let's page @vaa", by calling `/page @user`
- Habib: added me to the incident channel. Why? Maybe he noticed that me as a staff engineer was not added by default?
- Dmitry: ask yichen to drive RCA. Now I think Dmitry probably asked Habib to add me to the channel for help.
- Dmitry: updated the incident channel description with detailed impact: how many number of airflow tasks are affected, how many jobs are not impacted until what time.
