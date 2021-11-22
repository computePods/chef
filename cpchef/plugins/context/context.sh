# This shell script typesets a context document located at projectPath

if test $# -ne 2 ; then
  echo "usage: context.sh <documentName> <projectPath>"
  exit 1
fi

documentName=$1
projectPath=$2

#rsync -av $projectPath/* .

pwd

tree

context $documentName

#rsync -av . $projectPath
