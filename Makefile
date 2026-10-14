# From the project root: `make run` starts the CV path (see agents/README.md).
.PHONY: install run start doctor test

install run start doctor test:
	@$(MAKE) --no-print-directory -C agents $@
