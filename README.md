# Bring Me Image (experimental)

In the Gallery section of each model page on civitai.com, there are many images uploaded by regular users. If you often need to click on individual images and use the right-click to download them one by one, this project might be helpful for you.  
"Currently, it can only be used for images that are viewable without logging in (meaning it cannot access more restricted images)."

![sample1](examples/sample1_v0_1_0.png)

## Installation
(It is recommended to clone the repository within your virtual environment using Git)  
Use the git clone command to clone the repository.
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
![sample2](examples/sample2_v0_1_0.png)
1. Two checkboxes
   * CivitAI: Support copying hyperlinks of images in the Gallery (default checked).
   * Categorize: The image will be saved in the corresponding folder based on the model and version.
     * No guarantee of expected categorization
     * This feature needs to be used in conjunction with the "CivitAI" checkbox selected.
2. Clip
   * ![sample3](examples/sample3_v0_1_0.png)
   * The 'Clip' window will always stay on top, where you can start to begin the task.
   * "Start": Upon clicking, it will start detecting the links you have copied. After starting, the button will be renamed to "Stop," allowing you to pause the task. This means you can click "Start" again to resume.
   * "Display": If the link meets the format requirements, it will be added to the list, and the current number of additions will be displayed.
   * "Finish": After completing the task, click "Stop" first, and then click the button to return to the main window.
3. Clear
   * Once there is content in "Clip list", two checkboxes will be locked until the download task is completed. Clicking the button will clear the "Clip list" content and unlock the checkbox.
4. Which type of link should be copied?
   1. Checked the "CivitAI" checkbox:
      1. Copy the hyperlinks referred to by the images in the Gallery.
         * Taking Safari browser as an example, in the gallery section of the model, you can right-click on the desired image and select "Copy Link" to copy the link.
         * ![sample4](examples/sample4_v0_1_0.png)
      2. In fact, you can observe that these hyperlinks have the same format. If they do not match the format, a message will be displayed in the terminal.
         * "The matching format is `https://civitai.com/images/(number)`
   2. Unchecked the "CivitAI" checkbox:
      1. Copy the static link of the image. As long as you make sure to copy the static link of the image (supporting only .png, .jpg, .jpeg), it will work.
      2. If the link does not end with .png, .jpg, or .jpeg, a message will also be displayed in the terminal.
5. Save and Load "Clip list" Records
   1. Considering the high traffic on Civitai.com, if the server doesn't respond during the "Clipping" process, you can still complete and finish the "Clip" task. Afterwards, you can close the main window, and it will prompt you whether you want to save the list. Selecting 'Yes' will automatically save and close the window. (You can also save the records and keep the program running through 'Options > Save the Record'.)
   2. The saved file, which is a pickle file, will be stored in the same folder as main.py. It contains all the configuration parameters, so please avoid making any arbitrary modifications.
   3. Option > Load Clipboard File. Load Clip Records, you can resume the Clip task or click "GO" to start downloading.


## Test environment
```
Python 3.12
Macbook (OS 14.1)
```

## Additional note
The images content used in the instructions are sourced from civitai.com. If there are any concerns or issues, please let us know. Thank you.

## Supplementary note
The images are shared generously by many users. Please be mindful of the relevant copyright regulations when using them.

## Afterword
 Previously, image links on civitai.com included model and version information, making it easy to obtain the image paths directly through the official API.  
 Now, the links are generated through JavaScript events on the website, so Selenium is currently used to analyze the image links. The stability of this method is still being tested.  
 In future updates, login functionality will be added to access more restricted images.
