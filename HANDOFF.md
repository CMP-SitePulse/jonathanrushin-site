# HANDOFF.md

How to move this site from Marcus's GitHub to Jonathan's, so that Jonathan can run it himself through Claude. Claude: walk Jonathan through this one step at a time. Ask him to do each thing, wait for him to say it is done, then check it before moving on. Use plain English. Jonathan only ever uses his phone: the Claude iOS app (Code tab) and his phone browser. Every step below is written for that; never send him to a laptop or a terminal. Never create accounts for him, never ask him to paste a password into the chat, and never type one for him.

## Step 0. What he needs
Ask Jonathan to confirm he has, or is ready to get:
- A GitHub account (free).
- A Claude plan that includes Claude Code, and the Claude iOS app installed and signed in.
- Optional: his own GoDaddy account, if the domain is moving to him (recommended, see Step 5). The GoDaddy app or the phone browser both work.
Verify: he opens the Claude app and sees the Code tab.

## Step 1. Create his GitHub account
Ask him to open github.com in his phone browser, tap Sign up, and create the account himself with his own email and password. Suggest turning on two-factor authentication.
Ask him for his GitHub username (not the password).
Verify: https://github.com/<his-username> loads. Write the username down in lowercase; Steps 2 and 5 need it.

## Step 2. Marcus transfers the repo
Marcus does this part. Ask Jonathan to send him his GitHub username.
Marcus, on github.com/CMP-SitePulse/jonathanrushin-site: Settings > General, scroll to the Danger Zone, Transfer ownership. Choose "Specify an organization or username", enter Jonathan's username, type the repo name `jonathanrushin-site` to confirm, and transfer.
Jonathan then gets an email from GitHub. Ask him to open it on his phone, tap the link, and accept the transfer on github.com in the phone browser (signed in to his new account).
Verify: https://github.com/<his-username>/jonathanrushin-site exists and shows the files, and the CNAME file still says jonathanrushin.com. The live site may stop working until Steps 4 and 5 are done. That is expected.

## Step 3. Connect Claude Code to GitHub
Ask Jonathan to open the Code tab in the Claude app and look for the button to connect GitHub (if the app sends him to the browser, he finishes there). It installs the Claude GitHub app on his account. When GitHub asks which repositories to allow, he should pick "Only select repositories" and choose jonathanrushin-site.
Then ask him to pick jonathanrushin-site in the Code tab and start a new session there.
Verify: in that session you can see `CLAUDE.md`, `HANDOFF.md` and `src/index.html`, and `python3 -I src/build_site.py` runs clean. From here on you can continue this handoff from inside his repo.

## Step 4. Turn GitHub Pages back on
Pages settings often do not survive a transfer, so set them again even if they look right.
Ask Jonathan to open github.com/<his-username>/jonathanrushin-site/settings/pages in his phone browser. The mobile site often hides Settings; if the page does not show the Pages options, he switches to desktop-site mode (Safari: the aA button > Request Desktop Website) and reloads.
- Source: Deploy from a branch. Branch: main, folder: / (root). Save.
- Custom domain: jonathanrushin.com. Save.
- GitHub runs a DNS check. It may fail until Step 5 is done.
- Once the check passes and the certificate is issued, tick Enforce HTTPS.
Verify: he reads you, or sends a screenshot of, what the Pages page says. You want "Your site is live at https://jonathanrushin.com" and Enforce HTTPS ticked. If it is not there yet, do Step 5, then come back.

## Step 5. Point the domain at his account
One DNS record has to change: the www CNAME. The four A records stay as they are.

| Type | Name | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | `<his-username>.github.io` (all lowercase) |

Two ways to do it. Recommend option B so nothing depends on Marcus.

Option A, the domain stays with Marcus. Marcus signs in to GoDaddy, opens DNS for jonathanrushin.com, edits the CNAME named www, and changes it from cmp-sitepulse.github.io to `<his-username>.github.io`. Marcus keeps paying about $23 a year; it renews in February 2028.

Option B, the domain moves to Jonathan (recommended). Jonathan creates his own GoDaddy account if he has none, and gives Marcus his GoDaddy customer number or the email on that account. Marcus uses GoDaddy's "Transfer to another GoDaddy account" for jonathanrushin.com. It is free and the DNS records come with it. Jonathan accepts it in the GoDaddy app or the phone browser, then opens DNS for jonathanrushin.com there (in the app: the domain > DNS), and changes the www CNAME to `<his-username>.github.io`. He then owns the renewal, so ask him to turn on auto-renew.

Verify: ask him to read you, or screenshot, the DNS records in the GoDaddy app or phone browser. They should match the table exactly. Then go back to Step 4 and finish the DNS check and Enforce HTTPS.

## Step 6. Check the live site
Ask him to open each of these in his phone browser, or check them yourself if you can:
- https://jonathanrushin.com loads the site with the padlock.
- https://www.jonathanrushin.com ends up on https://jonathanrushin.com.
- http://jonathanrushin.com ends up on https://jonathanrushin.com.
Verify: all three land on the same page over https.

## Step 7. Instagram bio link
Ask him to make sure his Instagram (@j_rushin) bio link is https://jonathanrushin.com. He edits it in the Instagram app under Edit profile.
Verify: he says it is saved, and tapping it opens the site.

## Step 8. Marcus steps out
Once Steps 1 to 7 pass, check that nothing still depends on Marcus:
- Marcus is not listed under the repo's Settings > Collaborators (github.com/<his-username>/jonathanrushin-site/settings/access, desktop-site mode if needed). If he is, Jonathan removes him.
- The www CNAME no longer points at cmp-sitepulse.github.io.
- If option B was used, the domain is in Jonathan's GoDaddy account, not Marcus's.
- In `src/build_site.py`, update the README constant so the www row shows Jonathan's `<his-username>.github.io`, rebuild, and push. Do the same for the CNAME www row in `CLAUDE.md`.
Verify: tell Jonathan, in one short message, that the site, the code and the domain are now his.

## What can go wrong
- DNS check stays pending or fails. DNS changes can take up to an hour. Wait, then tap Check again on the Pages settings page. If it still fails, compare the GoDaddy records with the table above, letter by letter.
- Enforce HTTPS is greyed out. The certificate is not issued yet. Wait (often 15 minutes, sometimes longer), then refresh the Pages settings page.
- The site shows a GitHub 404 after the transfer. Pages is not turned on in his repo yet, or the custom domain is blank. Redo Step 4.
- The build fails. Read the error. It is usually a photo name that does not match its slot, or a width and height that no longer match the photo. Fix the cause; do not skip the check.

## Day to day
After the handoff Jonathan opens the Code tab in the Claude app, picks his repo, and says what he wants in plain words, for example: "change my phone number", "swap the hero photo for this one", "add a dish to the sample menu", or "update the guest count". Claude edits `src/index.html`, runs `python3 -I src/build_site.py`, shows him the new wording if it touches his career or cooking story, then commits and pushes to main and gives him https://jonathanrushin.com to check about a minute later.
New photo: Claude first asks him to attach it in the chat. If the attachment cannot be saved into the repo, he uploads it instead on github.com in his phone browser: open the repo, tap the `incoming` folder, Add file > Upload files, pick the photo, Commit changes (desktop-site mode if Add file is missing). He tells Claude which spot it is for. Claude moves it from `incoming/` into `src/photos-src/`, runs the image build and the site build, deletes the `incoming/` copy, and commits and pushes. The exact steps are in `CLAUDE.md` under Photos. He never needs a laptop or a terminal.
