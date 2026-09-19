; Common volume API. The patched game calls INT 82h instead of IN AL,60h.
; Game retains keyboard acknowledgement and IRQ1 EOI handling.
music_level dw 8
fx_level dw 8
volume_dirty db 1
key_scan db 0
key_hooked db 0
old82 dd 0
volume_keys times 4 dw 0
install_volume:
 mov ax,3582h
 int 21h
 mov [old82],bx
 mov [old82+2],es
 mov ax,2582h
 mov dx,volume_keyboard
 int 21h
 mov byte [key_hooked],1
 push cs
 pop es
 ret
remove_volume:
 cmp byte [key_hooked],0
 je .done
 push ds
 mov dx,[old82]
 mov ax,2582h
 mov ds,[old82+2]
 int 21h
 pop ds
.done: ret
volume_keyboard:
 push ax
 push bx
 push ds
 push cs
 pop ds
 in al,60h
 mov [key_scan],al
 cmp al,0bfh
 jb .make
 cmp al,0c2h
 jbe .consume
 jmp .done
.make:
 cmp al,3fh
 jb .done
 cmp al,42h
 ja .done
 movzx bx,al
 sub bx,3fh
 shl bx,1
 inc word [volume_keys+bx]
 cmp al,3fh
 je .music_down
 cmp al,40h
 je .music_up
 cmp al,41h
 je .fx_down
 cmp word [fx_level],10
 jae .consume
 inc word [fx_level]
 jmp .changed
.fx_down:
 cmp word [fx_level],0
 je .consume
 dec word [fx_level]
 jmp .changed
.music_up:
 cmp word [music_level],10
 jae .consume
 inc word [music_level]
 jmp .changed
.music_down:
 cmp word [music_level],0
 je .consume
 dec word [music_level]
.changed:
 mov byte [volume_dirty],1
.consume:
 mov byte [key_scan],0ffh ; ignored break code: reserve F5-F8 for volume
.done:
 pop ds
 pop bx
 pop ax
 mov al,[cs:key_scan]
 iret
volume_log:
 movzx eax,word [music_level]
 mov di,log_music_level
 call hex8
 movzx eax,word [fx_level]
 mov di,log_fx_level
 call hex8
 xor si,si
 mov di,log_volume_keys
.loop:
 movzx eax,word [volume_keys+si]
 call hex8
 inc di
 add si,2
 cmp si,8
 jb .loop
 ret
