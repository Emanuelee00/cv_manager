# From the project root: `make run` starts the CV path (see agents/README.md).
.PHONY: run start doctor test

run start doctor test:
	@$(MAKE) --no-print-directory -C agents $@
