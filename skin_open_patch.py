import re, subprocess

repo = '/Users/cc/Documents/deepseek-harness/default-workspace/_omega-port/repo'

# 1) add command variable next to Action_OSD_Main_OnDown
p = repo + '/1080i/Includes_Actions.xml'
t = open(p, encoding='utf-8').read()
anchor = '''    <variable name="Action_OSD_PVROSDGuide_OnDown">'''
assert anchor in t
block = '''    <!-- Open the OSD playlist with the focus already on the playing episode (helper add-on) -->
    <variable name="Action_OSD_Main_OnDown_Command">
        <value condition="$EXP[Exp_OSD_HasPlaylist] + !Skin.HasSetting(OSD.OnDown.Disable1140) + System.HasAddon(script.arcticfuse.focus)">RunScript(script.arcticfuse.focus,open,1140,7000)</value>
        <value>ActivateWindow($VAR[Action_OSD_Main_OnDown])</value>
    </variable>

'''
if 'Action_OSD_Main_OnDown_Command' not in t:
    t = t.replace(anchor, block + anchor, 1)
    open(p, 'w', encoding='utf-8').write(t)
    print('Includes_Actions: command variable added')

# 2) switch the three consumers
edits = 0
for rel in ('1080i/VideoOSD.xml', '1080i/Includes_OSD.xml'):
    p = repo + '/' + rel
    t = open(p, encoding='utf-8').read()
    old = '<ondown>ActivateWindow($VAR[Action_OSD_Main_OnDown])</ondown>'
    new = '<ondown>$VAR[Action_OSD_Main_OnDown_Command]</ondown>'
    count = t.count(old)
    if count:
        t = t.replace(old, new)
        open(p, 'w', encoding='utf-8').write(t)
        edits += count
        print(rel, 'consumers switched:', count)

# 3) version bump
p = repo + '/addon.xml'
t = open(p, encoding='utf-8').read()
t = t.replace('version="73.3.5.12"', 'version="73.3.5.13"', 1)
open(p, 'w', encoding='utf-8').write(t)
print('skin version -> 73.3.5.13, consumers total:', edits)
