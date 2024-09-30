"""
Since Civitai.com requires login to view sensitive images,
the following two variables are used to determine whether the automatic login is successful.
Here, the Login_Check_Url and Login_Check_Title of a sensitive model are selected, and no changes are normally needed.
If the model is removed, please manually update it to another sensitive model.
"""
Login_Check_Url = r'https://civitai.com/models/10364/innies-better-vulva'
Login_Check_Title = r'Innies: Better vulva - v1.1 | Stable Diffusion LoRA | Civitai'

"""
This is the default Chrome installation path for macOS. If it’s different, please modify it.
"""
Chrome_Path = r'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
