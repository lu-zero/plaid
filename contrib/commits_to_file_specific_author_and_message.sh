cd $1
git log --author=$3 --follow $2 | grep "$4"
