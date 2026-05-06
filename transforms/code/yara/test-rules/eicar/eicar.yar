/*
 * Minimal test rule: matches the EICAR anti-virus test string.
 * This is a standardized, harmless signature used to validate scanners.
 */

rule EICAR_Test_String
{
    meta:
        description = "EICAR anti-virus test string"
        author      = "DPK YARA transform tests"
        reference   = "https://www.eicar.org/download-anti-malware-testfile/"

    strings:
        $eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

    condition:
        $eicar
}
