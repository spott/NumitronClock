MEMORY {
    /* Pico 2: 4 MiB external flash, 512 KiB main SRAM. */
    FLASH : ORIGIN = 0x10000000, LENGTH = 4096K
    RAM   : ORIGIN = 0x20000000, LENGTH = 512K
}

/* Keep the RP2350 IMAGE_DEF within the boot ROM's first-4-KiB search window. */
SECTIONS {
    .start_block : ALIGN(4) {
        KEEP(*(.start_block));
        _stext = .;
    } > FLASH
} INSERT AFTER .vector_table;
