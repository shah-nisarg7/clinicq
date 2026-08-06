# clinic queue manager

built for a hack club project. It's a simple, zero cost queue management system for local clinics. Local clinics usually have messy waiting rooms, so this lets the receptionist track who is expected, who is waiting, and who is currently in the room.

Backend: google sheets api acting as a serverless database. it automatically creates a new sheet tab whenever a new clinic registers. The entire database is stored in a google spreadsheet, accessed by a service account of google cloud console.

whatsapp notifications: Couldnt implement real whatsapp API firing messages.. as it requires an established business (under government/ linking GST etc etc)after using multiple wayaround APIs i decided that  for this demo project ill keep  a log panel on the dashboard instead (just simulating what would be sent to patient and on what triggers)
# queue logic
Once the doctor starts the queue, each expected patient gets a live ETA calculated from how many people are ahead of them (in consult + waiting + still expected) times an average consult time, plus any doctor delay (before doctor arrives) the front desk enters manually which gets added to each patient's ETA

# How to run 
 Direct link : https://clinicq-three.vercel.app/
To register for a new account the secret code/admin code is set to "HACKCLUB_2026" (this was added in earlier version to prevent spamming whatsapp api through normal people testing it/using a bot..)


Running it locally would require cloning the repo then  a Google cloud service account (free) and generate service_account.json (from IAM and admin tab).
install dependencies by : pip install -r requirements.txt
set up .env file with ultramsg instance ID + token (still kept the code for API but currently no messages will be fired)
run it with vercel dev in terminal.
  
# Important points
Google sheets has limitations of approx 200 sheets, meaning 200 -3 (management tabs) ~ 197 clinics can register after which
google sheets cant handle it.
There is no rate limit currently, adding it would be a big task for login, register and adding a patient. 
