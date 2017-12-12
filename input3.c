#include<stdio.h>
#include<stdlib.h>

void banner(){
	printf("======================");puts("");
	printf("--------GuGuDan-------");puts("");
	printf("======================");puts("");
}
void main(){
	banner();
	for(int x=1;x<10;x++)
	{
		printf("=== %d Dan ===",x);puts("");
		for(int y=1;y<10;y++)
		{
			printf("%d * %d = %d",x, y, x*y);puts("");
		}
		printf("=============");puts("");
	}
}
