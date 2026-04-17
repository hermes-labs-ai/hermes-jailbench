# Security Policy

## Scope

`jailbreak-bench` is a defensive tool: a regression test suite for measuring LLM resistance to known refused patterns. It is intended for use by:

- Developers testing their own deployed models before production
- Red-team consultancies operating under signed engagement letters
- Researchers studying LLM safety under appropriate ethics review
- Enterprise AI governance teams running internal audits

Use against systems without authorization is outside the scope of support.

## Reporting a Vulnerability

If you discover a new attack pattern that bypasses safety on a production model and you believe the finding is significant enough to warrant coordinated disclosure:

- **Email**: security@hermes-labs.ai
- **Response target**: 72 hours for acknowledgement, 90 days for coordinated disclosure

For findings against third-party models (Claude, GPT, Gemini, etc.), we recommend contacting the vendor directly first. We are happy to help coordinate if useful.

## Responsible Use

When using this tool against vendor-hosted models:

- Respect rate limits (default `--delay 0.5s`; raise as needed).
- Do not attempt to bypass terms of service.
- Do not publish the verbatim output of compliance responses without responsible disclosure.
- Do not use for competitive intelligence against services you don't own.

The value of this tool is in the *negative-result corpus*: a known-refused baseline against which regressions can be measured. Any positive finding (a successful bypass) should go through the vendor's security process, not directly to this repo.

## Supported Versions

We patch security issues on the latest minor release. Older versions receive no security support.

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
