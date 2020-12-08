"""Export files from a git diff by using a zip file."""

import os
import sys
import zipfile
import subprocess

def clear():
    """Clear the current cmd"""
    os.system('cls' if os.name=='nt' else 'clear')

def expandpath(path):
    """Remove all path variables and returns an absolute path (relative to the 
    current working directory) for the given `path`.

    Parameters
    ----------
    path : str
        The path
    
    Returns
    -------
    str
        The expanded path
    """
    path = os.path.expanduser(os.path.expandvars(str(path)))
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    return os.path.normpath(os.path.abspath(path))

def execute():
    """Execute the program."""
    clear()
    # error messages
    error = None
    # whether the program was executed successfully or not
    success = False
    # the path the files are relative to
    rel_path = None
    # whether to close the files since it is a file object
    close_files = False
    # the comment to add to the zip file
    zip_comment = None

    if len(sys.argv) >= 2 and (str(sys.argv[1]).strip() in ("-t", "--txt")):
        if len(sys.argv) >= 3:
            # create the txt path
            txt_path = expandpath(sys.argv[2])
            rel_path = os.path.basename(txt_path)
            try:
                files = open(txt_path, "r")
                close_files = True
                print("Getting files from txt file {}".format(txt_path))
            except Exception as e:
                error = ("Could not open the file: {}: {}").format(
                            e.__class__.__name__, str(e))
            # set the zip path
            zip_path = sys.argv[1]
            # set the comment
            zip_comment = "Files defined by {}".format(txt_path)
        else:
            error = "Cannot find a txt file but -t switch is on."
    elif len(sys.argv) >= 3:
        # set the zip path
        zip_path = sys.argv[1]

        # create the git output from the diff
        if len(sys.argv) == 3:
            print("Getting files from diff {}..HEAD".format(sys.argv[2]))
            cmd = "git diff {} --name-only".format(sys.argv[2])
            # set the comment
            zip_comment = "Files defined by the diff of {}".format(sys.argv[2])
        elif len(sys.argv) >= 4:
            print("Getting files from diff {}..{}".format(sys.argv[2],
                                                          sys.argv[3]))
            cmd = "git diff {} {} --name-only".format(sys.argv[2], sys.argv[3])
            zip_comment = "Files defined by the diff between {} and {}".format(
                sys.argv[2], sys.argv[3])
        
        # execute the git command
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        out = process.stdout.read().decode("utf-8")

        # remove empty inputs, split the output
        files = list(filter(lambda x: x != "", out.split("\n")))
    else:
        error = "{} arguments are given but either 2 or 3 are required.".format(len(sys.argv))
    
    if error is None:
        print("Found {} files.".format(len(files)))
        print("Creating zip...")
        # expand the zip path
        zip_path = expandpath(zip_path)
        # the path the files should be relative to to create the directory
        # structure in the zip file
        rel_path = expandpath(os.getcwd())
        # the zip file
        zip_file = zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED)

        if isinstance(zip_comment, str):
            zip_file.comment = bytes(zip_comment, "utf-8")

        print("Copying into zip...")
        
        for source_path in files:
            source_path = expandpath(source_path)
            if rel_path in source_path:
                # the file is relative to the current working directory
                target_path = os.path.relpath(source_path, rel_path)
            else:
                # absoute file is outside of the current working directory so 
                # the file is copied to the zip root, this can only happen in 
                # the txt file mode
                print("  M '{}' - File is absolute, copying to zip root".format(source_path))
                target_path = os.path.basename(source_path)
            
            if os.path.isfile(source_path):
                zip_file.write(source_path, target_path)
                print("  S '{}' - Successfully added.".format(source_path))
            else:
                print("  F '{}' - File does not exist.".format(source_path))

        if close_files:
            files.close()
        zip_file.close()

        success = True
        print("Done.")

    if not success:
        title = "ziptxt"
        print(title)
        print("*" * len(title))
        print("")

        if isinstance(error, str):
            print("ERROR: {}".format(error))
            
        print("")
        print("Create a zip file from the git diff.")
        print("")
        print("usage: gitzip <zip path> [<from commit>] <to commit>")
        print("usage: gitzip -t <zip path> <txt file>")
        print("")
        print(("zip path:      The path to the zip file to create (with \n" + 
               "               extension), can be relative to the current \n" + 
               "               working directory."))
        print(("to commit,     The commits or branches to compare against \n" + 
               " from commit:  eachother, if one is omitted it is equal to \n" + 
               "               HEAD"))
        print(("-t, --txt:     Switch to the txt file mode (second usage)"))
        print(("txt file:      A path to a txt file containing paths \n" + 
               "               defining the files to add to the zip file, \n" + 
               "               all paths must be relative to the current \n" + 
               "               working directory, ignored if -t is off"))