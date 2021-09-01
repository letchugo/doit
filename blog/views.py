from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.text import slugify
from .models import Post, Category, Tag
from django.core.exceptions import PermissionDenied


class PostList(ListView):
    model = Post
    ordering = '-pk'

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        return context


class PostDetail(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        return context


class PostCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']

    def test_func(self):               # 펑션의 약자 / 유저테스트믹스사용시에 지원해줌
        return self.request.user.is_superuser or self.request.user.is_staff

    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated and (current_user.is_staff or current_user.is_superuser):
            form.instance.author = current_user   # 포스트를 만든 사람이다
            response = super(PostCreate, self).form_valid(form)
    # 폼 메소드가 post 방식으로 전달됨/ 그중에  tags_str라고 있을테니 담거라
            tags_str = self.request.POST.get('tags_str')
        # tags_str 있는 경우엔
            if tags_str:
                tags_str = tags_str.strip()         # strip : 스페이스없애주는것
                tags_str = tags_str.replace(',', ';')  # 컴마도 세미클론으로 바꿔줌 :모든걸 반영해주기위해
                tags_list = tags_str.split(';')   # 스플릿으로 쪼개주려고 함 ㅋㅋㅋ

                for t in tags_list:  # tags_list 로 for 문을 돌면서
                    t = t.strip()    # 앞뒤 공백 스페이스 없애주고
                    tag, is_tag_created = Tag.objects.get_or_create(name=t)
                    # 만약에 네임이 t 인거 있으면 가져오고 없으면 네임이 t 인걸로 만들어서 가져와라 get_or_create 는 2개의 결과값
                    if is_tag_created:
                        # 모델에 class tag 에 slug 채워줘야함  (한글 허용)
                        tag.slug = slugify(t, allow_unicode=True)
                        # tag 를 저장해야 태그를 slug 해서 slugify 한게 나옴
                        tag.save()
                        # 포스트에 tags 에 add 해야 tag 가 추가되는것
                    self.object.tags.add(tag)
                return response
        else:
                return redirect('/blog/')


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']
    template_name = 'blog/post_update_form.html'

    def get_context_data(self, **kwargs):
        context = super(PostUpdate, self).get_context_data()   # 기본적으로 업데이트뷰에서 제공하는 겟 컨텍스 사용하기 위한
        if self.object.tags.exists():   # 태그들이 다 있는 경우에
            tags_str_list = list()
            for t in self.object.tags.all():  # 이 포스트의 태그를 다가져와서
                tags_str_list.append(t.name)    # 태그의 이름을 리스트에 다담아
            context['tags_str_default'] = '; '.join(tags_str_list)    # 세미클론으로 조인
        return context

    def dispatch(self, request, *args, **kwargs):             # get 방식인지 post 방식인지 알아내는 역할
        # 유저가 로그인이 되어있으면 로그인사람과 get_object()pk로 들고와서 작성자와 비교
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:                # 장고에서 제공하는  200이 안뜨도록 기본적인 메세지 제공
            raise PermissionDenied

    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)
        # 폼베리드 기능추가 /form_valid() 함수는 유효한 폼 데이터로 처리할 로직 코딩/ django.http.HttpResponse 를 반환
        self.object.tags.clear()  # post 게시물 태그다 지움(delete 와 다름 (delete 는 db상 지움)/ 태그 연결을 끊어주는것)

        tags_str = self.request.POST.get('tags_str')

        # print("아무거나 찍어보자 ", self.request.POST.get('tags_str'))
        if tags_str:
            tags_str = tags_str.strip()  # strip : 스페이스없애주는것
            tags_str = tags_str.strip('; ')
            tags_str = tags_str.strip(', ')
            tags_str = tags_str.replace(',', ';')  # 컴마, 세미클론으로 바꿔줌 :모든걸 반영해주기위해
            tags_list = tags_str.split(';')

            for t in tags_list:  # tags_list 로 for 문을 돌면서
                t = t.strip()
                tag, is_tag_created = Tag.objects.get_or_create(name=t)
                if is_tag_created:
                    tag.slug = slugify(t, allow_unicode=True)
                    tag.save()
                self.object.tags.add(tag)

        return response


def category_page(request, slug):
    if slug == 'no_category':
        category = '미분류'
        post_list = Post.objects.filter(category=None)
    else:
        category = Category.objects.get(slug=slug)
        post_list = Post.objects.filter(category=category)

    return render(
        request,
        'blog/post_list.html',
        {
            'post_list': post_list,
            'categories': Category.objects.all(),
            'no_category_post_count': Post.objects.filter(category=None).count(),
            'category': category
        }
    )


def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)
    post_list = tag.post_set.all()

    return render(
        request,
        'blog/post_list.html',
        {
            'post_list': post_list,
            'tag': tag,
            'categories': Category.objects.all(),
            'no_category_post_count': Post.objects.filter(category=None).count(),
        }
    )



# def index(request):
#     posts = Post.objects.all().order_by('-pk')
#
#     return render(
#         request,
#         'blog/index.html',
#         {
#             'posts': posts,
#         }
#     )


# def single_post_page(request, pk):
#     post = Post.objects.get(pk=pk)
#
#     return render(
#         request,
#         'blog/single_post_page.html',
#         {
#             'post': post,
#         }
#     )
