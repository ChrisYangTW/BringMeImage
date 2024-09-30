# Bring Me Image

On each model page on civitai.com, there are many images uploaded by creators or regular users. If you often need to click on individual images and use the right-click to download them one by one, this project might be helpful for you.

![sample1](examples/sample1_v0_1_2.png)

## Installation 
Use the git clone command to clone the repository.  
(It is recommended to clone the repository within your virtual environment) 
```
git clone https://github.com/ChrisYangTW/BringMeImage.git
```
Switch to the folder where you have placed the repository,
and install the necessary dependencies.
```
pip3 install -r requirements.txt
```
Finally, run the main.py
```
python3 main.py
```

## Usage
![sample2](examples/sample2_v0_1_2.png)
1. One checkbox
   * CivitAI: Support copying hyperlinks of images in the Gallery (default checked).
   * When selecting the checkbox for CivitAI, regular static links such as .png, .jpg, and .jpeg can also be recognized. Unless you don’t need to recognize images from CivitAI, there’s no need to uncheck the box.
2. Clip
   * The 'Clip' window will always stay on top, where you can start to begin the task.
   * ![sample3](examples/sample3_v0_1_0.png)
   * "Start": Upon clicking, it will start detecting the links you have copied. After starting, the button will be renamed to "Stop," allowing you to pause the task. This means you can click "Start" again to resume.
   * "Display": If the link meets the format requirements, it will be added to the list, and the current number of additions will be displayed.
   * "Finish": After completing the task, click "Stop" first, and then click the button to return to the main window.
3. Clear
   * Once there is content in "Clip list", the 'CivitAI' checkbox will be locked until the download task is completed. Clicking the button will clear the "Clip list" content and unlock the checkbox.
4. Login
   * **Note: This program uses the system’s Chrome browser (you need to install it yourself beforehand)**
   * (No cookie file) The first time you login, a guide window will pop up
     * ![sample6](examples/sample6_v0_1_1.png)
       * Clicking "Open" will open the browser. After successful manual login, click "Finish".
       * Finally, the program will attempt automatic login again to ensure that the obtained cookies can be used for future automatic logins.
   * (Cookie file exist) Just double-clicking "Login" will trigger automatic login unless there are no available cookies.
5. Which type of link should be copied?
   1. Checked the "CivitAI" checkbox:
      1. Copy the hyperlinks referred to by the images.
         * Taking Safari browser as an example, you can right-click on the desired image and select "Copy Link" to copy the link.
         * ![sample4](examples/sample4_v0_1_0.png)
         * In fact, you can observe that these hyperlinks have the same format.
            * The matching format is `https://civitai.com/images/(number)`
      2. Copy the static link of the image. As long as you make sure to copy the static link of the image (supporting only .png, .jpg, .jpeg), it will work.
   2. Unchecked the "CivitAI" checkbox:
      * Only support the static link,
   3. If the link does not match the format, a message will be displayed in the terminal.
6. Save and Load "Clip list" Records
   1. Considering the high traffic on Civitai.com, if the server doesn't respond during the "Clipping" process, you can still complete and finish the "Clip" task. Afterward, you can close the main window, and it will prompt you whether you want to save the list. Selecting 'Yes' will automatically save and close the window. (You can also save the records actively. 'Options > Save the Record'.)
   2. The saved file, which is a pickle file, will be stored in the same folder as main.py.
   3. Option > Load Clipboard File. Load Clip Records, you can resume the Clip task or click "GO" to start downloading.
7. **Some configurations are in config.py(/BringMeImage/bringmeimage/config.py), and you need to check them before running this program for the first time.**


## Test environment
```
Python 3.12
Macbook (OS 15.0)
```

## Additional note
The images content used in the instructions are sourced from civitai.com. If there are any concerns or issues, please let us know. Thank you.

## Supplementary note
The images are shared generously by many users. Please be mindful of the relevant copyright regulations when using them.
