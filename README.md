# Bring Me Image (v0.1.0)
In the Gallery section of each model (each version) page on civitai.com, there are many images uploaded by regular users. If you often need to click on individual images and use the right-click to download them one by one, this project might be helpful for you.

![sample1](examples/sample1_v0_1_0.png)

## Installation
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

## Executable
You can use pyinstaller, py2app, py2exe to convert the code into an executable file that is compatible with the system.

## Usage
![sample2](examples/sample2_v0_1_0.png)
1. Two checkboxes
   * CivitAI: Support copying links of images in the Gallery (default checked).
   * Categorize: The image will be saved in the corresponding folder based on the model and version (default checked). This feature needs to be used in conjunction with the "CivitAI" checkbox selected.
2. Clicking on 'Clip' will pop up a window (which will always stay on top) where you can start copying links of your favorite images
   * ![sample3](examples/sample3_v0_1_0.png)
   * Start: Upon clicking, it will start detecting the links you have copied. After starting, the button will be renamed to "Stop," allowing you to pause the task. This means you can click "Start" again to resume.
   * Display: If the link meets the format requirements, it will be added to the list, and the current number of additions will be displayed.
   * Finish: After completing the copy task, click "Stop" first, and then click "Finish" to return to the main window.
3. Clear boutton
   * Once there is content in 'Clip', the checkbox will be locked until the download task is completed. Clicking the button will clear the 'Clip' content and unlock the checkbox.
4. Details
   1. Checked "CivitAI" checkbox:
      1. It means to copy the hyperlinks referred to by the images in the Gallery.
      2. Some browsers can copy the direct link of the image (i.e., the static link such as .jpeg). If you copy this type of link, it will not be added to the list.
      3. Taking Safari browser as an example, in the gallery section of the model, you can right-click on the desired image and select "Copy Link" to copy the link.
         * ![sample4](examples/sample4_v0_1_0.png)
      4. Of course, you can also click on the image and copy the link from the address bar.
         * ![sample5](examples/sample5_v0_1_0.png)
      5. In fact, it is specifically targeting URLs with a certain format in order to facilitate subsequent categorization and retrieval of the original images through an API.
         * ex: civitai.com/images/99999?...&modelVersionId=9999&modelId=9999&postId=9999
   2. Checked "Categorize" checkbox:
      1. As shown in the aforementioned item e, by parsing the URL and utilizing an API, it is possible to determine the model and version to which the image belongs, enabling the categorization of images into different folders accordingly.
      2. If the checkbox is not selected, all images will be placed in the folder you have set without categorization.
   3. Copying the direct static link of the image (without checking the "CivitAI" checkbox)
      1. At this point, you can directly copy the static URL of the image (only accepting .jpeg, .png, .jpg).
5. Other Features:
   1. Save and Load 'Clip' Records
      1. Considering the high traffic on Civitai.com, if the server doesn't respond while "Clipping," you can still complete the "Clip" task. You can close the main window, and it will prompt you whether you want to save the list. Selecting 'Yes' will automatically save and close the window.
      2. The saved file, which is a pickle file, will be stored in the same folder as main.py. It contains all the configuration parameters, so please avoid making any arbitrary modifications.
      3. Option > Load Clipboard File. Load Clip Records, you can resume the Clip task or click 'GO' to start downloading.
6. Example Video:
   1. Fetching images from the gallery
      * https://github.com/ChrisYangTW/BringMeImage/assets/127172524/16c21413-c9fc-493d-8612-d1c481013870
   2. Copying the static link of the image directly
      * https://github.com/ChrisYangTW/BringMeImage/assets/127172524/43a51f7b-801e-4b71-9ae3-6fc8c5ad926b
   3. Save and Load 'Clip' Records
      * https://github.com/ChrisYangTW/BringMeImage/assets/127172524/485d4948-8f31-4bc1-938f-dd6fcfc4d74f


## Test environment
```
Python 3.11
Macbook Pro16 M1 (OS Version 13.4 (22F66))
```

## Additional note
The images and video content used in the instructions are sourced from civitai.com. If there are any concerns or issues, please let us know. Thank you.

## Supplementary note
he images are shared generously by many users. Please be mindful of the relevant copyright regulations when using them.

## Afterword
 Initially, the intention was to directly download all the images from the galleries in the models. However, this approach turned out to be cumbersome when it came to selecting specific images. Therefore, based on personal browsing habits (Click on the image to load the static file of the image, and then right-click to download it.), this simple project was designed to facilitate downloading and management.  
 I believe a better approach would be to use programming to learn an individual's preferred image style and then automatically recognize and fetch images that match those characteristic values through web crawling.
