## Build a dev wheel ready to publish to pypi by merging one or more fork/branch into the latest dev branch
## This allows for the new code to go through functional, integration and regression testing before being merged to mainbranch
## Recommend using a clone from a fork (Running this from the main repo is not recommended)
## The command takes any number of parameters. Each parameter designates the fork and the branch being added to the test wheel
## Usage:
## git clone <fork>
## cd tansfdorms
## ../scripts/build-dev-pypi [fork1] branch1 [[fork2] branch2]+
## If fork is omitted, the current git repo is assumed
##  
## Examples
## cd transforms
##../scripts/build-dev-pypi.sh git@github.com:IBM/data-prep-kit.git docling-2.25 https://github.com/ian-cho/data-prep-kit.git dev dev3-testing
#./build-dev-pypi.sh git@github.com:IBM/data-prep-kit.git docling-2.25 dev3-testing
#../scripts/build-dev-pypi.sh git@github.com:ran-iwamoto/data-prep-kit.git issue1034 git@github.com:IBM/data-prep-kit.git tokenization2arrow_transform https://github.com/ian-cho/data-prep-kit.git dev dev2-testing


if ! [ -f "./pyproject.toml" ]; then
  echo
  echo "This script must be run from the transforms folder and the folder must contain pyproject.toml"
  echo
  exit
fi

### Create new branch to receive all merges. The branch will biscarded afterward
git checkout dev
git branch -D "testing-$(date '+%Y-%m-%d')"
git checkout -b "testing-$(date '+%Y-%m-%d')"
git branch



read -p "Press Enter to continue or ^C to abort..."
rm -fr build dist data_prep_toolkit_transforms.egg-info

i=1 
while [ $i ]; do
   # Does not matter what name we use, we just need a unique string for this run
   PR="PR$i"

   # Expect list of parameters starting with the git URL for the fork followed by the branch
   # ./build-dev-pypi.sh <fork_url1> <branch1> <fork_url1> <branch1>. 
   # Could also specify branch assuming origin from current form
   # ./build-dev-pypi.sh <fork_url1> <branch1> <branch2>. 
   fork="${!i}"
   if [[ -z "$fork" ]]; then break; fi
   if [[ $fork == git@github.com:* ]]  || [[ $fork ==  https://github.com* ]]; then
      ((i++))
      branch="${!i}"
      ((i++)) 
      if [[ -z "$branch" ]]; then echo "Missing branch..."; exit; fi
      git remote remove $PR
      git remote add $PR $fork
      git fetch $PR $branch
      git merge $PR/$branch
      if [ $? -ne 0 ]; then exit; fi
   else
      # We were not given a fork URL. Only a branch from this same repo
      branch=$fork
      #read -p "We were not given a fork URL. Only a branch ($branch) from this same repo..."
      git merge origin/$branch
      if [ $? -ne 0 ]; then exit; fi
      ((i++)) 
   fi
done

make build-pkg-dist
#uv pip install twine
#make publish-dist



