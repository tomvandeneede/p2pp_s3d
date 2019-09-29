# p2pp - **Palette2 Post Processing tool for Simplify 3D  (S3D)**


## Changelog

- 21/09/2019 - Initial release 0.0.1


# Purpose

Allow users to generate mcf.gcode files directly from within the S3D environment and making used of some of the advanced possibilities of 
S3D


**IMPORTANT:**

This is new development and a lot of the S3D features should be tested before being used.  At this point only single layer heights are supported



# Setting up S3D

```

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
At this early state there is very little error checking on the parameters and settings within S3D.  
Make sure to get S3Dsetup correctly to avoid generating unprintable files 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```


1. Setup S3D for use with P2 as you would for use with Chroma
2. Under Additions, **ENABLE** the purge tower.   At this moment p2pp/s3d is not able to position the tower by itself and since there is no
graphical interface to allow the user to position the tower, this needs to be done from within S3D.   The purge tower generated by 3D will be replaced by an entirely new purge tower
3. Under the GCode tab  enter the correct dimensions of your printer
4. Also under the Gcode Tab, make sure that the "Relative extrusion distances" option is checked
5. Run the script without any parameters.  This will return the full path to the script that you can use in the post processing script box
under the scripts tab  you will need to add the following parameter @[output_filepath]
6. Go to the scripts tab and locate the Starting Script sub tab.   Here you will do the big chunck of p2pp configuration:
7. Make sure that the Autoconfiguration for print settings are the same for ALL layers.   S3D will generate incomplete header information in case of mixing

Here is a sample section with some explanation of this configuration

```
    ;Palette 2 Configuration 
    ;P2PP PRINTERPROFILE=e827315ff39d9c78
    ;P2PP SPLICEOFFSET=40
    ;P2PP MINSTARTSPLICE=100
    ;P2PP MINSPLICE=70
    ;P2PP LINEARPINGLENGTH=350
    
    ; tool purge length information for p2pp
    ;P2PP TOOL_0=PLA:[80;90]
    ;P2PP TOOL_1=PLA:[80;100]
    ;P2PP TOOL_2=PLA:[80;120]
    ;P2PP TOOL_3=PLA:[80;130]
    
    ; Material splicing profile information
    ;P2PP MATERIAL_DEFAULT_0_0_0
    ;P2PP MATERIAL_PVA_PVA_0_0_0
    ;P2PP MATERIAL_PVA_PLA_0_0_0
    ;P2PP MATERIAL_PLA_PLA_0_0_0
```

>**PRINTERPROFILE **[MANDATRY]
links the gcode to a specific printer that is setup within your Palette 2.  
The ID has to ba a seauence of 16 characters from the following character set [0-9a-f]

>**TOOL_n=FIL:[unload;load]**  [MANDATORY]
the TOOL command provides basic info on the filament used.   One line must be issues for EACH of the inputs used.
The first parameter n specifies the input.  n ranges from  0 to 3. 
The second parameter specifies the type of filament.  The abbreviation here MUST be the same abbreviation of filament type
used in the MATERIAL descriptions!  Examples for filament type are PLA, PETG, PVA, ABS, HIPS, ....
Behind the colon there are 2 parameters separated bij a coma.  Both are INTEGER values.  The first describes the unload length
to be used when switching to a next value... Higher values indicate stronger filament so more bleeding into the next.  The second value 
describes the loading purge, the amount of filament to be purged when loading this filament.   Higher values indicate a weaker filament coolor
that is more susceptible to bleeding. 
The actual purge length is the average of the unloading lengt of the old filament and the loading length of the new filament.




> **MATERIAL_XXX_XXX\_#\_#\_#**[OPTIONAL]
    This is used to to define heat/compression/cooling settings for the splice between materials. 
    The MATERIAL_DEFAULT setting provides a configurable fallback in case no profile is defined for the material combination. 
    Please be aware that entries are not symmetrical and you need to define the settings for both directions in 
    order to specify a complete process. The definition is as per standard Chroma and Canvas profiles. 
    Order of parameters is CURRENT-MATERIAL/NEW-MATERIAL/HEAT/COMPRESSION/COOLING. 
    Default is all 0 as per standard in Chroma and Canvas.
    
   ```
  ;P2PP MATERIAL_PLA_PLA_0_0_0
  ``` 

> **EXTRAENDFILAMENT=ppp\#** *[OPTIONAL]*
  This parameter is used to configure the extra length (in mm) of filament
  P2 will generate at the end of the print.  The default parameter value is defined as 150mm.  
  The value should at least be the length between the extruder motor to the nozzle. 
  
   ```
  ;P2PP EXTRAENDFILAMENT=150
  ```

> **LINEARPINGLENGTH=nnnn**  *[OPTIONAL]*
    This is used to keep the filament disctance between pings constant to nnnn mm.  
    When this parameter is not set, the ping distance is exponentially growing during the print 
    resulting in filament distances up to 3m between pings in very long prints.  
    ** WARNING ** Some users have reported issues when setting LINEARPINGLENGTH to values below 350mm.  
    It is suggested to keep 350mm as a minimum.
   ```
  ;P2PP LINEARPINGLENGTH=350
  ```  
  > **SPLICEOFFSET=nnn[%]** *[OPTIONAL]*
    Splice offset indicates the amount of filament the splice is scheduled after ending printing with a specific tool.
    The value can be set to a fixed number in milimeter or a percentage of the purge length applied
    
   ```
   ; use 30mm splice offset for all splices
  ;P2PP SPLICEOFFSET=30
  
  or 
  
  ; use a variable splice offset set to 30% of the transition length
  ;P2PP SPLICEOFFSET=30%
  ``` 
  
  
  ![splice offset](https://github.com/tomvandeneede/p2pp/blob/master/docs/spliceoffset.png)
  
  
## Make a donation...

If you like this software and want to support its development you can make a small donation to support me in maintaining and expanding the capabilities p2pp for simplify 3D.

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=t.vandeneede@pandora.be&lc=EU&item_name=Donation+to+P2PP+Developer&no_note=0&cn=&currency_code=EUR&bn=PP-DonationsBF:btn_donateCC_LG.gif:NonHosted)



## **Good luck & happy printing !!!**
  
