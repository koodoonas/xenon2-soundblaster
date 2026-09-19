bits 16
cpu 386
org 100h
jmp start
banner db 13,10,'Xenon II - experimental digital audio',13,10,13,10
 db '  1  Sound Blaster (DSP 2.0+, BLASTER, 3 MB free EMS)',13,10
 db '  2  Gravis UltraSound (ULTRASND, 512 KB free EMS)',13,10
 db '  Esc / Q  Exit',13,10,13,10
 db 'During gameplay: F5/F6 music -/+   F7/F8 effects -/+',13,10
 db 'Volumes start at 80%; 10% steps, 0=mute, 100%=maximum.',13,10
 db 'Select 1 or 2: $'
error db 13,10,'Unable to launch audio driver. Keep all package files together.',13,10,'$'
sb db 'X2SB.COM',0
gus db 'X2GUS.COM',0
tail db 0,13
params dw 0,tail,0,5ch,0,6ch,0
saved_sp dw 0
start:
 mov ax,cs
 mov ds,ax
 mov es,ax
 cli
 mov ss,ax
 mov sp,stack_end
 sti
 mov bx,(end-$$+100h+15)/16
 mov ah,4ah
 int 21h
 jc fail
 mov dx,banner
 mov ah,9
 int 21h
.key:
 xor ah,ah
 int 16h
 cmp al,27
 je quit
 or al,20h
 cmp al,'q'
 je quit
 cmp al,'1'
 je .sb
 cmp al,'2'
 jne .key
 mov dx,gus
 jmp .run
.sb:
 mov dx,sb
.run:
 mov ax,cs
 mov [params+4],ax
 mov [params+8],ax
 mov [params+12],ax
 mov [saved_sp],sp
 mov bx,params
 mov ax,4b00h
 int 21h
 cli
 mov bx,cs
 mov ds,bx
 mov es,bx
 mov ss,bx
 mov sp,[saved_sp]
 sti
 jc fail
 mov ah,4dh
 int 21h
 mov ah,4ch
 int 21h
quit:
 mov ax,4c00h
 int 21h
fail:
 mov dx,error
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
stack times 512 db 0
stack_end:
end:
