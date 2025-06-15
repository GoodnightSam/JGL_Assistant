1) Create Original script - o3
   Create ElevenLabs (phonetic) script - o3/o4 mini

2) Create Video plan - o3
	- Break down script into 3 - 10 second chunks
	- Give description of 3 descriptions of most engaging instrumental music that would engage target audience
	- For Each chunk:
		- Assign 1 x AI generated Image Midjourney description for visually stunning/relevant images for each 
		- Assign 1 x KlingAI/Veo 2 AI generated video description based on the AI generated Image for a visually engaging video clip
		- Assign 1 x Image search term for each chunk.

3) Get Images (Bing & Google Image Search API)
	- Bing API (1000 free requests/month)
		- 200 Searches/Week
		- Up to 150 image urls PER SEARCH
	- Google API (100 free searches/day)
		- Up to 20 image urls PER SEARCH

4) Download images to actor name folder
	- Use python to save image URLS
	
5) Vet images using Gemini Pro (~$0.30)
	- Have Gemini Pro choose best 3 images per script chunk
	- All unused images are moved to archive folder

6) Create AI-Generated Images ($1 - Stability/GPT-4o/Replicate PRUNAAI)
	- Create 4 different image variations for all chunks of intro script.
	- Create 1 image for all other chunks of script.
		- DreamStudio SDXL: $0.36 for 45 HD images
		- GPT Image 1: $3.10 for 45 HD images
		- Replicate SD “cheetah”: $1.35 for 45 HD images

7) Custom local webtool (Python) (20 minutes)
	- Open HR Image chooser tool
	- Each actor folder will have it's own JSON? file that it will use.
	- It will run through each script chunk and display the best 4 images.
	- User will choose which image (images) to keep with checkmarks
		- User can also flag an image for upscaling, and fixing aspect ratio (seperately if needed)
	- User will then navigate to the next chunk and do this for all chunks.
	- After user completes choosing image(s) for each chunk. The JSON file is then completed and processed.
		- All images not used are moved to the archive folder.
		- Images are renamed to the script text chunk number they were chosen for. If there are multiple images chosen, then they are named with an a,b,c,etc. as part of their name (e.g 5a.jpg, 5b.png, 5c.jpg, etc)
		- Images flagged for upscaling and/or fixing the aspect ratio are sent via API to Flux Kontext. Upscaling first, AND THEN aspect ratio.

8) AI video clips (Veo2, PikaLabs, KlingAI) - (60-90mins - human?)
	- Intro and select clips throughout
		- When and how to choose which clips throughout?
	- PikaLabs ($35/month)
		- 21 x 5-second clips/week
	- Veo2 ($20 storage plan)
		- 1000 creds - 10 creds/Veo2 Fast 5 second)
		- 11 x 5-sec videos/week (2 attempts)
	- KlingAI ($8.80/month) 6/week
		- 660 Creds/month
		- Kling 1.6 (Start & End frames)
			- 20 Creds Standard (35 cred pro) 5 seconds
		- Kling 2.1 (Start, BUT NO End Frame)
			- 20 Creds Standard (35 cred pro) 5 seconds
		- 6 x 5-sec videos/week
   
9) Eleven Labs script narrator production ($22/month) (20 mins - human)
	- Download to asset folder

10) Suno song generation ($8/ month) (15 mins - human)
	- Take 3 song descriptions and process them (6 music options)
	- Choose best song and download to project asset folder.

11) Filmora ($10/month) (60-90mins - human?)
	- Create Template the makes things as easy as possible (Need to research and figure out if anything can be done programmatically with this)
	- Put assets into Filmora
	- Edit video

12) Create thumbnail (30 mins - human)
	- Can probably get this down to 30 mins with a template
	- Need to figure out best standardized ideation and creation flow for this

13) Upload and fill out YouTube video details
	- Should have o3 include this in it's original video plans so that I can copy and paste this in.
