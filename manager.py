#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os
import modslibrary
from cryptography.fernet import Fernet
import pickle


# Constants
class Cnst:

    try:
        with open('creds.bin', 'rb') as fp:
            ENC_CREDENTIALS = pickle.load(fp)
            fernet = Fernet(ENC_CREDENTIALS[1])
            CREDENTIALS = fernet.decrypt(ENC_CREDENTIALS[0])

    except FileNotFoundError:
        key = Fernet.generate_key()
        fernet = Fernet(key)

        print("\n\n\nNon è stato trovato il file contenente l'utente Steam. Inseriscilo ora.\n")

        username_tmp = bytes(input('Inserisci username di Steam: '), encoding='utf8')
        password_tmp = bytes(input('Inserisci password di Steam: '), encoding='utf8')

        CREDENTIALS = str(username_tmp) + " " + str(password_tmp)
        ENC_CREDENTIALS = fernet.encrypt(username_tmp + b" " + password_tmp)

        with open('creds.bin', 'wb') as fp:
            pickle.dump([ENC_CREDENTIALS, key], fp)

    GAME_ID = "107410"
    SERVER_ID = "233780"
    
    GAME_FOLDER = "/home/arma/a3server/"
    GAME_MODS_FOLDER = GAME_FOLDER + "mods/"
    GAME_MISSIONS_FOLDER = GAME_FOLDER + "mpmissions/"
    STARTUP_SCRIPTS_FOLDER = GAME_FOLDER + "startup/"

    STEAM_FOLDER = '/home/arma/Steam/'
    STEAM_MODS_FOLDER = STEAM_FOLDER + 'steamapps/workshop/content/107410/'

    SCRIPTS_FOLDER = "/home/arma/scripts/"
    CALL_STEAMCMD = ["./steamcmd.sh", "+login " + str(CREDENTIALS)]
    SCRIPT_UPDATE_SERVER = ['+runscript', 'force_install_dir /home/arma/a3server', 'app_update 233780 validate']
    CALL_SCREEN_ARMA = ["screen", "-S", "arma"]
    CD_GAME_FOLDER = "cd " + GAME_FOLDER


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


update_mods = []

for mod_t in modslibrary.mods:
    mod_tmp = str(mod_t[0])
    cmd_mod = "+workshop_download_item " + Cnst.GAME_ID + " " + mod_tmp + " "
    update_mods += cmd_mod
update_mods += ["validate", "+quit"]


def run_steamcmd(script):

    os.chdir(Cnst.STEAM_FOLDER)
    subprocess.call(Cnst.CALL_STEAMCMD + [script])


def manage_mods_list(mods):
    # Creates a temp file to use with steamcmd and creates a symlink

    fp = open(Cnst.SCRIPTS_FOLDER + "mods.txt", "w+")

    for tupla in mods:
        # Add the new string to a temp file
        mod_id = str(tupla[0])         # mod id from the workshop
        mod_name = str(tupla[1])        # custom name for the symlink
        cmd_mod = "workshop_download_item " + Cnst.GAME_ID + " " + mod_id + " validate\n"
        fp.write(cmd_mod)

        # Does that symlinking thing
        old_mod_folder = Cnst.STEAM_MODS_FOLDER + mod_id
        new_mod_folder = Cnst.GAME_MODS_FOLDER + "@" + mod_name
        try:
            os.symlink(old_mod_folder, new_mod_folder)
        except OSError:
            print("Mod already linked")

    fp.write("quit")
    fp.close()


def fix_uppercase(dir_path):
    # Since arma on linux is broken af, it can't read mods with files named with uppercase letters'
    for path, subdirs, files in os.walk(dir_path):
        for name in files:
            path_old = os.path.join(path, name)
            path_new = os.path.join(path, name.lower())
            print(path_new)
            os.rename(path_old, path_new)

####################################################################################################################

# TODO meccanismo di backup
# TODO meccanismo di creazione nuova missione


choice = 0

print('\n\n\n')
print(Colors.BOLD + "========================================================\n\tMANAGER SERVER\n========================================================" + Colors.ENDC)
while choice != 6:
    print("1) Start server\n2) Aggiorna server\n3) Aggiungi setup missione\n4) Aggiorna mods\n5) Aggiorna mod specifica\n6) Esci")
    choice = int(input("Scegli un'opzione: "))
    print("\n")

    # Start server
    if choice == 1:

        index = 1
        startup_scripts = os.listdir(Cnst.STARTUP_SCRIPTS_FOLDER)
        for script in startup_scripts:
            print(str(index) + ") " + script)
            index += 1

        startup_choice = int(input("Scegli una missione: "))
        startup_script = startup_scripts[startup_choice - 1]

        os.chdir(Cnst.STARTUP_SCRIPTS_FOLDER)
        fp = open(Cnst.STARTUP_SCRIPTS_FOLDER + str(startup_script), 'r')

        script_string = fp.read()
        fp.close()

        # Creates a new screen
        script_bash = 'screen -S arma -dm bash -c "' + Cnst.CD_GAME_FOLDER + "; " + script_string + '"'

        subprocess.Popen(script_bash, shell=True).wait()
        print(Colors.OKGREEN + "Avvio del server in corso..." + Colors.ENDC)

    # Update server
    if choice == 2:

        # generate script for a split second and deletes it. Really wonky but I don't care
        fp_upd = open(Cnst.SCRIPTS_FOLDER + "s_upd.txt", 'w')
        fp_upd.write('@ShutdownOnFailedCommand 1\n@NoPromptForPassword 1\nlogin ' + str(Cnst.CREDENTIALS) + "\nforce_install_dir " + Cnst.GAME_FOLDER + "\napp_update " + Cnst.SERVER_ID + " validate\nquit")
        script = "+runscript " + Cnst.SCRIPTS_FOLDER + "s_upd.txt"
        run_steamcmd(script)
        os.remove(Cnst.SCRIPTS_FOLDER + "s_upd.txt")

    # Add a new mission
    if choice == 3:

        print(" !!!INCOMPLETA!!!")
        # Creates a whole new cfg file with a default configuration
        mission_list = os.listdir(Cnst.GAME_MISSIONS_FOLDER)
        index = 1
        for mission in mission_list:
            print(str(index) + ") " + mission)
            index += 1
        
        print(str(index) + ") Missione aggiuntiva")
        mission_choice = int(input("Scegli una missione da aggiungere: "))

        # In case the mission wasn't in that folder, but inside another modded pbo or something
        if mission_choice == index:
            mission_name = int(input("Inserire nome missione: "))
        else:
            mission_name = mission_list[mission_choice - 1]


        # Open the default cfg and copy it in cfg
        #TODO Add it
        fp_default = open("", "r")
        default_cfg = fp_default.read()
        fp_default.close()

        # Create a new custom file for the cfg
        startup_file_name = str(input("Inserire nome nuova istanza: "))

        fp_new_cfg = open("..", "w")        
        fp_new_cfg.write(default_cfg)
        fp_new_cfg.close()

        # Choosing the mods for this instance

        #TODO Prints a list of the currently downloaded mods

    # Update mods
    if choice == 4:
        
        manage_mods_list(modslibrary.mods)
        script = "+runscript " + Cnst.SCRIPTS_FOLDER + "mods.txt"
        run_steamcmd(script)
        os.remove(Cnst.SCRIPTS_FOLDER + "mods.txt")     # Just to clear stuff
        fix_uppercase(Cnst.STEAM_MODS_FOLDER)

    # Update single mod
    if choice == 5:

        mod_id = int(input("Inserire id mod: "))
        mod_name = str(input("Inserire nome mod: "))    # used raw_input before, not sure why. Probably older python?
        temp_list = [(mod_id, mod_name,)]
        manage_mods_list(temp_list)
        script = "+runscript " + Cnst.SCRIPTS_FOLDER + "mods.txt"
        run_steamcmd(script)
        os.remove(Cnst.SCRIPTS_FOLDER + "mods.txt")     # Just to clear stuff
        fix_uppercase(Cnst.STEAM_MODS_FOLDER + str(mod_id))

    # Quit the manager
    if choice == 6:
        quit()
    
    print("\n")
