; Xenon II Sound Blaster PCM launcher prototype. NASM, DOS .COM, 386+.
; Original game copy calls INT 81h; native INT 80h retains PC speaker FX.
; EMS holds the complete unsigned 8-bit mono PCM track. No DOS calls in IRQ.
bits 16
cpu 386
org 100h
jmp start

sb_base dw 220h
sb_irq db 7
sb_dma db 1
irq_vector db 0fh
irq_mask db 80h
old_pic db 0
old_irq dd 0
old_81 dd 0
ems_handle dw 0ffffh
ems_frame dw 0
ems_pages dw 0
file_handle dw 0ffffh
dma_alloc dw 0
dma_seg dw 0
dma_page db 0
dma_addr dw 0
dma_port db 83h
file_size dd 0
song_pos dd 0
start_pos dd 0
irq_count dd 0
loop_count dd 0
fill_count dd 0
start_count dw 0
stop_count dw 0
fx_count dw 0
ems_errors dw 0
exec_error dw 0
irq_installed db 0
hook_installed db 0
dsp_ok db 0
dsp_major db 0
dsp_minor db 0
playing db 0
started db 0
half dw 0
mode db 0
old_mixer db 0
mixer_saved db 0
saved_ss dw 0
saved_sp dw 0
parent_ss dw 0
parent_sp dw 0
last_status db 0
fill_left dw 0
fill_chunk dw 0
exit_code db 0

msg_title db 'Xenon II Sound Blaster prototype - loading PCM into EMS...',13,10,'$'
msg_ready db 'Sound Blaster ready. Launching X2SB.EXE.',13,10,'$'
msg_test db 'PCM test: eight seconds (Esc to stop).',13,10,'$'
msg_done db 'Sound Blaster stopped; resources restored. See X2SB.LOG.',13,10,'$'
msg_ems db 'EMS unavailable or insufficient: enable at least 3 MB EMS.',13,10,'$'
msg_file db 'Cannot load X2MUSIC.PCM (raw unsigned 8-bit mono PCM).',13,10,'$'
msg_memory db 'Not enough conventional memory for the DMA buffer.',13,10,'$'
msg_sb db 'Sound Blaster DSP 2.0+ not detected at BLASTER base address.',13,10,'$'
msg_config db 'Supported BLASTER settings: IRQ 5 or 7; DMA 0, 1 or 3.',13,10,'$'
msg_exec db 'Could not execute X2SB.EXE. See X2SB.LOG.',13,10,'$'
file_pcm db 'X2MUSIC.PCM',0
file_exe db 'X2SB.EXE',0
file_log db 'X2SB.LOG',0
blaster_name db 'BLASTER='
empty_tail db 0,13
exec_block dw 0,empty_tail,0,5ch,0,6ch,0

start:
 cli
 mov ax,cs
 mov ds,ax
 mov es,ax
 mov ss,ax
 mov sp,stack_end
 sti
 cld
 mov bx,(resident_end-$$+100h+15)/16
 mov ah,4ah
 int 21h
 jc error_memory
 ; /TEST and /LOOPTEST use the same bounded, standalone playback test.
 mov si,81h
 movzx cx,byte [80h]
.scan_args:
 jcxz .args_done
 lodsb
 and al,0dfh
 cmp al,'T'
 jne .not_t
 cmp byte [mode],0
 jne .not_t
 mov byte [mode],1
.not_t:
 cmp al,'L'
 jne .next_arg
 mov byte [mode],2
.next_arg:
 loop .scan_args
.args_done:
 call parse_blaster
 jc error_config
 mov dx,msg_title
 call print
 call load_pcm
 jc error_ems_or_file
 call alloc_dma
 jc error_memory
 call reset_dsp
 jc error_sb
 mov byte [dsp_ok],1
 mov al,0e1h
 call dsp_write
 jc error_sb
 call dsp_read
 jc error_sb
 mov [dsp_major],al
 call dsp_read
 jc error_sb
 mov [dsp_minor],al
 cmp byte [dsp_major],2
 jb error_sb
 call install_irq
 call install_hook
 cmp byte [mode],0
 jne standalone
 mov dx,msg_ready
 call print
 mov ax,cs
 mov [exec_block+4],ax
 mov [exec_block+8],ax
 mov [exec_block+12],ax
 mov [parent_ss],ss
 mov [parent_sp],sp
 mov bx,exec_block
 mov dx,file_exe
 mov ax,4b00h
 int 21h
 ; Old DOS versions need SS:SP restored after EXEC.
 cli
 mov bx,cs
 mov ds,bx
 mov es,bx
 mov ss,[parent_ss]
 mov sp,[parent_sp]
 sti
 jnc .executed
 mov [exec_error],ax
 mov dx,msg_exec
 call print
 mov byte [exit_code],1
.executed:
 jmp finish

standalone:
 cmp byte [mode],2
 jne .play
 mov eax,[file_size]
 sub eax,6000
 jc error_file
 mov [start_pos],eax
.play:
 mov dx,msg_test
 call print
 call sb_start
 xor ax,ax
 mov es,ax
 mov bx,[es:046ch]
.wait:
 mov ah,1
 int 16h
 jz .clock
 xor ah,ah
 int 16h
 cmp al,27
 je finish
.clock:
 mov ax,[es:046ch]
 sub ax,bx
 cmp ax,146
 jb .wait
 jmp finish

error_ems_or_file:
 cmp byte [last_status],1
 je error_file
 mov dx,msg_ems
 jmp error
error_file: mov dx,msg_file
 jmp error
error_memory: mov dx,msg_memory
 jmp error
error_sb: mov dx,msg_sb
 jmp error
error_config: mov dx,msg_config
error:
 call print
 mov byte [exit_code],1
finish:
 call cleanup
 call write_log
 mov dx,msg_done
 call print
 mov al,[exit_code]
 mov ah,4ch
 int 21h

print:
 mov ah,9
 int 21h
 ret

; Search the DOS environment. Parse A as hex, I/D as decimal.
parse_blaster:
 push es
 mov es,[2ch]
 xor di,di
.env:
 cmp byte [es:di],0
 je .validate
 push di
 mov si,blaster_name
 mov cx,8
 repe cmpsb
 pop di
 je .found
.skip:
 cmp byte [es:di],0
 lea di,[di+1]
 jne .skip
 jmp .env
.found:
 add di,8
.token:
 mov al,[es:di]
 inc di
 test al,al
 jz .validate
 and al,0dfh
 cmp al,'A'
 je .address
 cmp al,'I'
 je .irq
 cmp al,'D'
 je .dma
 jmp .token
.address:
 mov bp,16
 call number
 mov [sb_base],bx
 jmp .token
.irq:
 mov bp,10
 call number
 mov [sb_irq],bl
 jmp .token
.dma:
 mov bp,10
 call number
 mov [sb_dma],bl
 jmp .token
.validate:
 pop es
 cmp word [sb_base],210h
 jb .bad
 cmp word [sb_base],280h
 ja .bad
 test word [sb_base],0fh
 jnz .bad
 mov al,[sb_irq]
 cmp al,5
 je .valid_irq
 cmp al,7
 jne .bad
.valid_irq:
 add al,8
 mov [irq_vector],al
 mov cl,[sb_irq]
 mov al,1
 shl al,cl
 mov [irq_mask],al
 mov al,[sb_dma]
 cmp al,0
 je .dma0
 cmp al,1
 je .ok
 cmp al,3
 jne .bad
 mov byte [dma_port],82h
 jmp .ok
.dma0:
 mov byte [dma_port],87h
.ok:
 clc
 ret
.bad:
 stc
 ret
number:
 xor bx,bx
.loop:
 movzx ax,byte [es:di]
 cmp al,'0'
 jb .done
 cmp al,'9'
 jbe .digit
 and al,0dfh
 cmp al,'A'
 jb .done
 cmp al,'F'
 ja .done
 sub al,7
.digit:
 sub al,'0'
 cmp ax,bp
 jae .done
 imul bx,bp
 add bx,ax
 inc di
 jmp .loop
.done:
 ret

load_pcm:
 mov byte [last_status],1
 mov ax,3d00h
 mov dx,file_pcm
 int 21h
 jc .bad
 mov [file_handle],ax
 mov bx,ax
 xor cx,cx
 xor dx,dx
 mov ax,4202h
 int 21h
 jc .bad
 mov [file_size],ax
 mov [file_size+2],dx
 cmp dword [file_size],8192
 jb .bad
 cmp dword [file_size],4000000
 ja .bad
 xor cx,cx
 xor dx,dx
 mov ax,4200h
 int 21h
 jc .bad
 mov byte [last_status],2
 ; EMM signature at offset 0Ah in the INT 67 handler segment.
 mov ax,3567h
 int 21h
 cmp dword [es:0ah],'EMMX'
 jne .bad
 cmp dword [es:0eh],'XXX0'
 jne .bad
 mov ah,40h
 int 67h
 test ah,ah
 jnz .bad
 mov ah,41h
 int 67h
 test ah,ah
 jnz .bad
 mov [ems_frame],bx
 mov eax,[file_size]
 add eax,16383
 shr eax,14
 mov [ems_pages],ax
 mov bx,ax
 mov ah,43h
 int 67h
 test ah,ah
 jnz .bad
 mov [ems_handle],dx
 mov ah,47h
 int 67h
 test ah,ah
 jnz .bad
 xor bp,bp
.pages:
 mov dx,[ems_handle]
 mov bx,bp
 mov ax,4400h
 int 67h
 test ah,ah
 jnz .restore_bad
 ; Fill page padding with unsigned PCM silence.
 mov es,[ems_frame]
 xor di,di
 mov ax,8080h
 mov cx,8192
 rep stosw
 mov bx,[file_handle]
 mov eax,[file_size]
 movzx ecx,bp
 shl ecx,14
 sub eax,ecx
 cmp eax,16384
 jbe .read_size
 mov ax,16384
.read_size:
 mov cx,ax
 mov [fill_chunk],cx
 xor dx,dx
 push ds
 mov ds,[ems_frame]
 mov ah,3fh
 int 21h
 pop ds
 jc .read_bad
 cmp ax,[fill_chunk]
 jne .read_bad
 inc bp
 cmp bp,[ems_pages]
 jb .pages
 mov ah,48h
 mov dx,[ems_handle]
 int 67h
 test ah,ah
 jnz .bad
 mov bx,[file_handle]
 mov ah,3eh
 int 21h
 mov word [file_handle],0ffffh
 push cs
 pop es
 clc
 ret
.read_bad:
 mov byte [last_status],1
.restore_bad:
 mov ah,48h
 mov dx,[ems_handle]
 int 67h
.bad:
 push cs
 pop es
 stc
 ret

alloc_dma:
 mov bx,1024 ; 16K allocation always contains an 8K non-crossing DMA window.
 mov ah,48h
 int 21h
 jc .bad
 mov [dma_alloc],ax
 mov bx,ax
 shl bx,4
 cmp bx,0e000h
 jbe .fits
 add ax,0fffh
 and ax,0f000h
.fits:
 mov [dma_seg],ax
 movzx eax,ax
 shl eax,4
 mov [dma_addr],ax
 shr eax,16
 mov [dma_page],al
 clc
.bad:
 ret

reset_dsp:
 mov dx,[sb_base]
 add dx,6
 mov al,1
 out dx,al
 mov cx,64
.delay:
 in al,dx
 loop .delay
 xor al,al
 out dx,al
 call dsp_read
 jc .bad
 cmp al,0aah
 jne .bad
 clc
 ret
.bad: stc
 ret

dsp_read:
 push cx
 push dx
 mov dx,[sb_base]
 add dx,0eh
 mov cx,0ffffh
.wait:
 in al,dx
 test al,80h
 jnz .ready
 loop .wait
 stc
 jmp .done
.ready:
 sub dx,4
 in al,dx
 clc
.done:
 pop dx
 pop cx
 ret

dsp_write:
 push ax
 push cx
 push dx
 mov ah,al
 mov dx,[cs:sb_base]
 add dx,0ch
 mov cx,0ffffh
.wait:
 in al,dx
 test al,80h
 jz .ready
 loop .wait
 stc
 jmp .done
.ready:
 mov al,ah
 out dx,al
 clc
.done:
 pop dx
 pop cx
 pop ax
 ret

install_irq:
 mov al,[irq_vector]
 mov ah,35h
 int 21h
 mov [old_irq],bx
 mov [old_irq+2],es
 mov al,[irq_vector]
 mov ah,25h
 mov dx,sb_isr
 int 21h
 in al,21h
 mov [old_pic],al
 mov byte [irq_installed],1
 ; Ensure SB Pro mixer is in mono mode; restore it on exit.
 cmp byte [dsp_major],3
 jb .done
 mov dx,[sb_base]
 add dx,4
 mov al,0eh
 out dx,al
 inc dx
 in al,dx
 mov [old_mixer],al
 and al,0fdh
 out dx,al
 mov byte [mixer_saved],1
.done:
 push cs
 pop es
 ret

install_hook:
 mov ax,3581h
 int 21h
 mov [old_81],bx
 mov [old_81+2],es
 mov ax,2581h
 mov dx,sound_hook
 int 21h
 mov byte [hook_installed],1
 push cs
 pop es
 ret

sound_hook:
 cmp ah,2
 je .song
 cmp ah,1
 je .stop
 cmp ah,4
 je .resume
 cmp ah,3
 jne .native
 inc word [cs:fx_count]
.native:
 int 80h
 iret
.song:
 test al,al
 jnz .stop
 ; Keep original initialization/API side effects, then mute native music only.
 int 80h
 push ax
 mov ax,2000h
 int 80h
 pushad
 push ds
 push es
 push cs
 pop ds
 call sb_start
 pop es
 pop ds
 popad
 pop ax
 iret
.stop:
 pushad
 push ds
 push es
 push cs
 pop ds
 call sb_stop
 pop es
 pop ds
 popad
 jmp .native
.resume:
 cmp byte [cs:started],0
 je .native
 push ax
 mov al,0d4h
 call dsp_write
 mov byte [cs:playing],1
 pop ax
 int 80h
 push ax
 mov ax,2000h
 int 80h
 pop ax
 iret

sb_start:
 pushf
 cli
 inc word [start_count]
 mov al,0d0h
 call dsp_write
 ; Mask the DMA channel before reprogramming.
 mov al,[sb_dma]
 or al,4
 out 0ah,al
 mov eax,[start_pos]
 mov [song_pos],eax
 xor di,di
 call fill_half
 cmp word [ems_errors],0
 jne .failed
 mov di,4096
 call fill_half
 cmp word [ems_errors],0
 jne .failed
 mov word [half],0
 xor al,al
 out 0ch,al
 mov al,[sb_dma]
 or al,58h ; single transfer, auto-init, memory -> device
 out 0bh,al
 xor dx,dx
 mov dl,[sb_dma]
 shl dl,1
 mov ax,[dma_addr]
 out dx,al
 mov al,ah
 out dx,al
 inc dx
 mov ax,8191
 out dx,al
 mov al,ah
 out dx,al
 mov dl,[dma_port]
 mov al,[dma_page]
 out dx,al
 mov al,[sb_dma]
 out 0ah,al
 ; Reset time constant on each start: 1,000,000 / (256-165) = 10989.011 Hz.
 mov al,40h
 call dsp_write
 mov al,165
 call dsp_write
 mov al,48h
 call dsp_write
 mov al,0ffh
 call dsp_write
 mov al,0fh ; interrupt every 4096 bytes
 call dsp_write
 mov al,0d1h
 call dsp_write
 mov byte [playing],1
 mov byte [started],1
 mov al,1ch
 call dsp_write
 in al,21h
 mov ah,[irq_mask]
 not ah
 and al,ah
 out 21h,al
 popf
 ret
.failed:
 mov byte [exit_code],1
 popf
 ret

sb_stop:
 pushf
 cli
 inc word [stop_count]
 mov byte [playing],0
 cmp byte [dsp_ok],0
 je .done
 mov al,0d0h
 call dsp_write
.done:
 popf
 ret

; DI selects the half of the DMA buffer. All EMS maps are restored on return.
fill_half:
 pushad
 push ds
 push es
 cld
 mov word [fill_left],4096
 mov dx,[ems_handle]
 mov ah,47h
 int 67h
 test ah,ah
 jnz .error_no_map
.copy:
 mov eax,[song_pos]
 cmp eax,[file_size]
 jb .not_end
 xor eax,eax
 mov [song_pos],eax
 inc dword [loop_count]
.not_end:
 mov esi,eax
 and si,3fffh
 and esi,0ffffh
 shr eax,14
 mov bx,ax
 mov dx,[ems_handle]
 mov ax,4400h
 int 67h
 test ah,ah
 jnz .error_map
 mov ax,16384
 sub ax,si
 cmp ax,[fill_left]
 jbe .page_limit
 mov ax,[fill_left]
.page_limit:
 movzx ecx,ax
 mov eax,[file_size]
 sub eax,[song_pos]
 cmp eax,ecx
 jae .size_limit
 mov cx,ax
.size_limit:
 mov [fill_chunk],cx
 mov es,[dma_seg]
 push ds
 mov ds,[ems_frame]
 rep movsb
 pop ds
 movzx eax,word [fill_chunk]
 add [song_pos],eax
 sub [fill_left],ax
 jnz .copy
 inc dword [fill_count]
 mov ah,48h
 mov dx,[ems_handle]
 int 67h
 test ah,ah
 jnz .error_no_map
 jmp .done
.error_map:
 mov ah,48h
 mov dx,[ems_handle]
 int 67h
.error_no_map:
 inc word [ems_errors]
 mov byte [exit_code],1
 mov byte [playing],0
 mov al,0d0h
 call dsp_write
 ; Clear the remainder to avoid exposing stale data on a failed map.
 mov es,[dma_seg]
 mov cx,[fill_left]
 mov al,80h
 rep stosb
.done:
 pop es
 pop ds
 popad
 ret

sb_isr:
 push ax
 mov ax,ss
 mov [cs:saved_ss],ax
 mov [cs:saved_sp],sp
 mov ax,cs
 mov ss,ax
 mov sp,irq_stack_end
 pushad
 push ds
 push es
 push cs
 pop ds
 cld
 inc dword [irq_count]
 mov dx,[sb_base]
 add dx,0eh
 in al,dx ; acknowledge the 8-bit DSP interrupt
 cmp byte [playing],0
 je .ack
 mov di,[half]
 call fill_half
 xor word [half],4096
.ack:
 mov al,20h
 out 20h,al
 pop es
 pop ds
 popad
 mov ax,[cs:saved_ss]
 mov ss,ax
 mov sp,[cs:saved_sp]
 pop ax
 iret

cleanup:
 call sb_stop
 cmp byte [dsp_ok],0
 je .vectors
 mov al,0d3h
 call dsp_write
 call reset_dsp
 mov al,[sb_dma]
 or al,4
 out 0ah,al
 cmp byte [mixer_saved],0
 je .vectors
 mov dx,[sb_base]
 add dx,4
 mov al,0eh
 out dx,al
 inc dx
 mov al,[old_mixer]
 out dx,al
.vectors:
 cmp byte [irq_installed],0
 je .hook
 cli
 in al,21h
 mov ah,[irq_mask]
 not ah
 and al,ah
 mov ah,[old_pic]
 and ah,[irq_mask]
 or al,ah
 out 21h,al
 sti
 push ds
 mov dx,[old_irq]
 mov al,[irq_vector]
 mov ah,25h
 mov ds,[old_irq+2]
 int 21h
 pop ds
.hook:
 cmp byte [hook_installed],0
 je .ems
 push ds
 mov dx,[old_81]
 mov ax,2581h
 mov ds,[old_81+2]
 int 21h
 pop ds
.ems:
 mov dx,[ems_handle]
 cmp dx,0ffffh
 je .file
 mov ah,45h
 int 67h
.file:
 mov bx,[file_handle]
 cmp bx,0ffffh
 je .buffer
 mov ah,3eh
 int 21h
.buffer:
 mov ax,[dma_alloc]
 test ax,ax
 jz .done
 mov es,ax
 mov ah,49h
 int 21h
.done:
 push cs
 pop es
 ret

write_log:
 movzx eax,word [sb_base]
 mov di,log_base
 call hex8
 movzx eax,byte [sb_irq]
 mov di,log_irq
 call hex8
 movzx eax,byte [sb_dma]
 mov di,log_dma
 call hex8
 movzx eax,byte [dsp_major]
 shl eax,8
 mov al,[dsp_minor]
 mov di,log_dsp
 call hex8
 mov eax,[irq_count]
 mov di,log_irqs
 call hex8
 mov eax,[loop_count]
 mov di,log_loops
 call hex8
 mov eax,[fill_count]
 mov di,log_fills
 call hex8
 movzx eax,word [start_count]
 mov di,log_starts
 call hex8
 movzx eax,word [stop_count]
 mov di,log_stops
 call hex8
 movzx eax,word [fx_count]
 mov di,log_fx
 call hex8
 movzx eax,word [ems_errors]
 mov di,log_errors
 call hex8
 movzx eax,word [exec_error]
 mov di,log_exec
 call hex8
 movzx eax,word [dma_seg]
 shl eax,4
 mov di,log_buffer
 call hex8
 mov eax,[file_size]
 mov di,log_size
 call hex8
 xor cx,cx
 mov dx,file_log
 mov ah,3ch
 int 21h
 jc .done
 mov bx,ax
 mov dx,log_start
 mov cx,log_end-log_start
 mov ah,40h
 int 21h
 mov ah,3eh
 int 21h
.done: ret
hex8:
 mov cx,8
.loop:
 rol eax,4
 mov bl,al
 and bl,15
 add bl,'0'
 cmp bl,'9'
 jbe .digit
 add bl,7
.digit:
 mov [di],bl
 inc di
 loop .loop
 ret
log_start db 'X2SB prototype diagnostics (hexadecimal values)',13,10,'Base='
log_base db '00000000',13,10,'IRQ='
log_irq db '00000000',13,10,'DMA='
log_dma db '00000000',13,10,'DSP major/minor='
log_dsp db '00000000',13,10,'DMA interrupts='
log_irqs db '00000000',13,10,'PCM wraps='
log_loops db '00000000',13,10,'DMA half fills='
log_fills db '00000000',13,10,'Music starts='
log_starts db '00000000',13,10,'Music stops='
log_stops db '00000000',13,10,'Speaker FX requests='
log_fx db '00000000',13,10,'EMS errors='
log_errors db '00000000',13,10,'EXEC error='
log_exec db '00000000',13,10,'DMA physical address='
log_buffer db '00000000',13,10,'PCM byte count='
log_size db '00000000',13,10
log_end:
align 16
irq_stack times 1024 db 0
irq_stack_end:
stack times 2048 db 0
stack_end:
resident_end:
