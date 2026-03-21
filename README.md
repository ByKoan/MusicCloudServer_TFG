# MusicCloudServer_TFG

>`Project version: 2.4`  (This value will be updated on every funcionality change in the project)

> ***About this version: In the last version, Added funcionality to find songs/videos from youtube and play the audio using yt_dlp, and fixed problem with playlist while changing the name of the playlist***


> This project is under license. Please check the LICENSE file for legal information. Feel free to use the program, but be aware of the license policy, as any type of commercial use is explicitly prohibited. It is delivered without warranty, and any changes, modifications, or integrations will be the property of the original author. The author of this project is not responsible for any problems the software may cause, and any changes or modifications to the project must include the original author's name and do not necessarily require notification.

**MusicCloudServer is the project that allow you to make your own private server to play the music you want with complete freedom. No ads, connected with youtube and you can upload your own audio files (download from youtube too!)**

## Information about the project:

- The objective of this project is to get freedom enjoying your music. This is a final degree project not finished yet, where you can currently listen to music you've downloaded and uploaded with complete freedom.

- This project is raised to connect whenever and anywhere. First of all the firewall in your local machine where running the project will need to be able for listen in the port 8080 (Web Server port used), then you can expose your local network to connect from the exterior or used a private VPN to connect from the IP it gave you. I reccomend the last one if you more privacy.

    - VPN recommended: https://www.zerotier.com (Free 3 Networks and 10 Devices)

- Future implementations that will be made:
    - ~~user role management (database protection)~~
    - ~~user stats (Database)~~
    - ~~server stats (System usage) (Operative Systems) - Will be used to check minimum requirements to run the project~~
    - ~~local playlists (Database)~~
    - ~~route to play audio/videos from youtube (Web/App)~~
    - funcionality that allow to download audio from youtube automatically 
    - importing youtube playlists
    -  desktop application (App)
    - mobile application (App)

## Use and desplegation of the project:

***This project is multiplatform:***

- In Windows you will need Docker to run it (For easier deployment):
    - You will find in the root path a file called `BuildDocker.bat`, it will drop down the containers if they already exists and build it. The Dockerfile is responsible for installing dependencies, exposing ports etc. The docker-compose.yml create the containers, networks etc.

    - Run the `BuildDocker.bat` or run this in a **CMD**:

    ```bash
    docker compose down -v
    docker compose build --no-cache
    docker compose up
    ```

    - It will create the containers: 1 for the web service and another for the DataBase (`MySQL`)

- In Linux you will need to setup your own MySQL server, when you setup the server configure the variables in .env with your user and password. You will need to change the music folder with the path you will put the local music files too

## Project Structure:

- ***All the code is finded on `src` root***

### `main.py`:

- This class is the main class of the project, it create the `Flask` app, create the **DB**, sincronyze the local music with the **DB** and register all the *Blueprints* of the routes. (For debugging print all routes after the start of the app)
- It runs on `http://<vm_ip>:8080`. Recommend to usea a private VPN to access to the service everywhere you are 

### `config.py`:

- This class is the main config class for the app. It contains the following variables:
	- `secret_key` - Secret key for `flask` app
	- `db_user` - db user
	- `db_password` - db password
	- `db_name` - db name
	- `db_host` - db host
	- `base_music_folder` - root where users folder will be created
	- `allowed_extensions` - allowed extensions for audio files

### `.env`:

- Environment variables file
### `/utils`:

- Here will be some utilities used in the project
#### `/utils/file_utils.py`:

- This is a function that will check if the file extension is valid on `allowed_extensions`

### `/templates`:

- Here will be the `html` files of the routes
#### `login.html`: 
- Login panel
#### `index.html`:
- Root panel (Show the local songs view)
#### `admin_panel.html`:
- Show the admin panel (You need privilegies with the user rol)
#### `playlists`:
- Page to create playlists
#### `playlist_view.html`:
- Show the songs of the playlist indicated
#### `upload.html`:
- Page to upload songs file to local audio files
#### `youtube.html`:
- Page to play songs from youtube and download it
### `/static`:

- Root with the styles and javascript files
#### `styles.css`:
- styles for the html pages
#### `player.js`:
- main javascript file for the project (need to refactor separating the code)
#### `youtube.js`:
- javascript file for handling the youtube functions
### `/services`:

- Here will be located service to handle some data with the db
#### `music_service.py`:
- Obtains the user folder and the user songs
#### `auth_service.py`:
- Validate the the user to the db
### `/routes`:

- Here will be located all the python files of the routes

#### `/routes/auth_routes.py`:
- This route is used to make the login **POST**, it obtains the `username` and the `password` from the `html` inputs and validate if the user is banned, if the user is banned, shows a log on the login `div` that say the time the user is banned, if not it will try to validate the credentials to the db. If it get succes, redirect to `index` if not reload the login. This file contains to the `/logout` route
#### `/routes/music_routes.py`:
- `music_routes` is the file that contains the routes that is used on the index of the server. It contains the following routes:

	- `"/"` index route that shows the index of the server. it validates if the user is logged if not redirect to `login.html`. It shows all the user songs and all other items 

	- `"/play/<filename>"` route to play a song from the local files, it validates if the user is logged if not redirect to `login.html`. At same time update the server stats while playing the song. If try to play a song that does not exist it will throw an `404 error`

	- `"/delete_song"` route to delete songs from local files. it validates if the user is logged if not redirect to `login.html`. if the file does not exist throw an `400 error`, if exist try to delete it from `DB` and `local`, if it doesn't exist in either of the two places throw an `500 error`
#### `/routes/upload_routes`:
- This route will be used only to upload songs to play them on local. It validates if the user is logged, if not, redirect to `login.html`. It makes a **POST** request with the file and upload it to local files and the name of the song to the **DB**, also update server stats when upload songs.
- It validates.
	- If the file does not exists
	- If not files selected 
	- If is not an allowed file

#### `/routes/admin_routes.py`:
- This file is dedicated only to **admin routes**, you will need admin perms.
- This file have the following routes:

	- `"/"`: Main route of the admin routes, it will show up the `html` of the page showing all sections. Contains methods **GET** and **POST**. This route let you create users, search them, show the system stats

	- `"/change_role/<username>"`: Route dedicated to change the role of a user. Contains method **POST**

	- `"/delete/<username>"`: Route dedicated to delete users. Contains method **POST**

	- `"/ban_user"`: Route dedicated to ban users. Contains method **POST**

	- `"/unban_user"`: Route dedicated to unban users. Contains method **POST**

	- `"/change_password/<username>"`: Route dedicated to change the password of the users. Contains methos **POST**

	- `"/system_stats"`: Route dedicated to get the system stats

#### `/routes/playlist_routes`:
- This file is dedicated only to **playlist routes** (*All playlist system is managed from DB*)
- This file have the following routes:

	- `"/playlists"`: Check if user is logged, if not redirect to `login.html`. Obtain and shows all playlist from database

	- `"/create_playlist"`: Check if user is logged, if not redirect to `login.html`. Contains method **POST**, creates the playlist in database

	- `"/playlist/<int:playlist_id>"`: Check if user is logged, if not redirect to `login.html`. Access to the playlist clicked/selected

	- `"/delete_playlist"`: Check if user is logged, if not redirect to `login.html`. Contains method **POST**, delete the playlist and the songs it have asigned (not the local files and the record in table songs) of the database

	- `"/rename_playlist"`: Check if user is logged, if not redirect to `login.html`. Contains method **POST**, rename the playlist from database

#### `/routes/add_to_playlist.py`:
- This file is dedicates to manage the route that is dedicate to add local songs to playlist:
	- `/add_to_playlist` Contains method **POST**. Check if user is logged, if not redirect to Login. Check if the `filename` or the `playlist_id` are not setted, if not send an **400 ERROR**  . Update the db adding the song to the `playlist_songs` table. If the song dont exist on the db or exists already in the playlist it will send an **404 ERROR** or **409 ERROR** 

#### `/routes/remove_from_playlist`:
- This file is dedicated to manage the route that is dedicated to remove local songs from the playlist:
	- `/remove_from_playlist`: Contains method **POST**. Check if user is logged, if not redirect to login. Check if the `filename` or the `playlist_id` are not setted, if not send an **400 ERROR** . Check if the user is the owner of the playlist, if not send an **404 ERROR**, check if the song dont exists on the playlist, if not send an **404 ERROR**. Update table `playlist_songs` deleting the song

#### `routes/youtube_page.py`:
- This file contains some routes asociated to youtube funcionalities: (**TO DO**)
	- `/youtube_page`:

	 - `/youtube_search`:

	- `/youtube_audio`:

	- `/youtube_download`:

### `/resources`:

#### `manage_database_script.py`:
- Script dedicated to manage the DB in cli manually.
#### `script.sql`:
- Script with the DB schema to create it. It contains a record with the firt user (admin) `koan:koan`
#### `sync_music_db.py`:
- Script to sync the local song files with the DB records
### `/db`:
#### `db.py`:

- Script that allow the project to manage the DB and get the info