#!/bin/sh

echo " Running NEAT tests"
echo "########################################"

PREFIX=$1
EXAMPLES_DIR="../examples"
RC_GLOBAL=0

##############

echo ""
echo "HTTP-Client requesting from bsd10"
echo "########################################"
$PREFIX$EXAMPLES_DIR/client_http_get -u /cgi-bin/he bsd10.nplab.de
echo ""
RC=$?
if [[ $RC != 0 ]]; then
    RC_GLOBAL=1
    echo ">> test failed!"
else
    echo ">> test succeeded"
fi

##############

echo ""
echo "HTTP-Client requesting from bsd10"
echo "########################################"
$PREFIX$EXAMPLES_DIR/client_http_get -u /cgi-bin/he 212.201.121.100
echo ""
RC=$?
if [[ $RC != 0 ]]; then
    RC_GLOBAL=1
    echo ">> test failed!"
else
    echo ">> test succeeded"
fi

##############

echo ""
echo "HTTP-Client requesting from bsd10"
echo "########################################"
$PREFIX$EXAMPLES_DIR/client_http_get -u /cgi-bin/he 2a02:c6a0:4015:10::100
echo ""
RC=$?
if [[ $RC != 0 ]]; then
    RC_GLOBAL=1
    echo ">> test failed!"
else
    echo ">> test succeeded"
fi

##############

echo ""
echo "HTTP-Client requesting from bsd10"
echo "########################################"
$PREFIX$EXAMPLES_DIR/client_http_get -u /cgi-bin/he not.resolvable.neat
RC=$?
echo ""
if [[ $RC != 1 ]]; then
    RC_GLOBAL=1
    echo ">> RC $RC - test failed!"
else
    echo ">> RC $RC - test succeeded"
fi

return $RC_GLOBAL
